#!/usr/bin/env python

import logging, os
import math, numpy as np, cv2, tf.transformations

import utils
import pdb

def round_pt(p): return (int(p[0]), int(p[1]))

class SMoCap:

    def __init__(self):
        self.lower_red_hue_range = np.array([0,  100,100]), np.array([10,255,255]) 
        self.upper_red_hue_range = np.array([160,100,100]), np.array([179,255,255])
        params = cv2.SimpleBlobDetector_Params()
        # Change thresholds
        params.minThreshold = 2;
        params.maxThreshold = 256;
        # Filter by Area.
        params.filterByArea = True
        params.minArea = 2
        # Filter by Circularity
        params.filterByCircularity = True
        params.minCircularity = 0.1
        # Filter by Convexity
        params.filterByConvexity = True
        params.minConvexity = 0.5
        # Filter by Inertia
        params.filterByInertia = True
        params.minInertiaRatio = 0.5
        self.detector = cv2.SimpleBlobDetector_create(params)

        self.markers_body = np.array([[0, 0, 0.155, 1.], [0, 0.045, 0.155, 1.], [0, -0.045, 0.155, 1.], [0.04, 0., 0.155, 1.]])
        self.markers_names = ['c', 'l', 'r', 'f']
        self.marker_c, self.marker_l, self.marker_r, self.marker_f = range(4)
        self.world_to_cam_T, self.world_to_cam_t, self.world_to_cam_q, self.world_to_cam_r = None, None, None, None
        self.irm_to_body_T = np.eye(4)
        self.irm_to_body_T[2,3] = 0.15
        
        self.K = np.array([[476.7030836014194, 0.0, 400.5],
                           [0.0, 476.7030836014194, 400.5],
                           [0.0, 0.0, 1.0]])
        self.D = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        self.invK =  np.linalg.inv(self.K)
        


    def set_world_to_cam(self, world_to_camo_t, world_to_camo_q):
        print('setting world_to_cam {} {}'.format(world_to_camo_t, world_to_camo_q))
        self.world_to_cam_t, self.world_to_cam_q = world_to_camo_t, world_to_camo_q 
        self.world_to_cam_T = utils.T_of_quat_t(world_to_camo_q, world_to_camo_t)
        self.world_to_cam_r, foo = cv2.Rodrigues(self.world_to_cam_T[:3,:3])

    def detect_keypoints(self, img):
        if 0:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mask1 = cv2.inRange(hsv, *self.lower_red_hue_range)
            #mask2 = cv2.inRange(hsv, *self.upper_red_hue_range)
            self.keypoints = self.detector.detect(255-mask1)
        else:
            self.keypoints = self.detector.detect(255-img)
        #print('detected img points\n{}'.format(np.array([kp.pt for kp in keypoints])))
        self.detected_kp_img = np.array([kp.pt for kp in self.keypoints])
        return self.keypoints

    def keypoints_detected(self):
        return len(self.detected_kp_img) == 4

    def keypoints_identified(self):
        return False
     
    
    def identify_keypoints(self):
        ''' naive identification of markers '''
        if len(self.detected_kp_img) != 4: return
        self.marker_of_kp = np.array([-2, -2, -2, -2])
        # first use distance to discriminate center and front
        dists = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                dists[i, j] = np.linalg.norm(self.detected_kp_img[i]- self.detected_kp_img[j])
        #print('dists {}'.format(dists))
        sum_dists = np.sum(dists, axis=1)
        #print('sum dists {}'.format(sum_dists))
        sorted_idx = np.argsort(sum_dists)
        #print sorted_idx
        self.marker_of_kp[sorted_idx[0]] = self.marker_c
        self.marker_of_kp[sorted_idx[1]] = self.marker_f
        # now use vector product to discriminate right and left
        cf = self.detected_kp_img[sorted_idx[1]] - self.detected_kp_img[sorted_idx[0]]
        c2 = self.detected_kp_img[sorted_idx[2]] - self.detected_kp_img[sorted_idx[0]]
        #c3 = self.detected_kp_img[sorted_idx[3]] - self.detected_kp_img[sorted_idx[0]]
        def vprod(a, b): return a[0]*b[1]-a[1]*b[0]
        s2 = vprod(cf, c2)
        #s3 = vprod(cf, c3)
        #print 's2 s3', s2, s3
        if s2 > 0:
            self.marker_of_kp[sorted_idx[2]] = self.marker_r
            self.marker_of_kp[sorted_idx[3]] = self.marker_l
        else:
            self.marker_of_kp[sorted_idx[2]] = self.marker_l
            self.marker_of_kp[sorted_idx[3]] = self.marker_r
        self.kp_of_marker = np.argsort(self.marker_of_kp)
        #print self.marker_of_kp


        
    def track_foo(self):
        h, status = cv2.findHomography(self.detected_kp_img[self.kp_of_marker], self.markers_body[:,:2])
        #h, status = cv2.findHomography(self.markers_body[:,:2], self.detected_kp_img[self.kp_of_marker])
        #h, status = cv2.findHomography(self.detected_kp_img[self.markers_of_kp], self.markers_body[:,:2])
        invC = np.linalg.inv(self.K)
        h1, h2, h3 = h[:,0], h[:,1], h[:,2] 
        _lambda = 1./np.linalg.norm(np.dot(invC, h1))
        #_lambda = 1./np.linalg.norm(np.dot(invC, h2))
        r1 = _lambda*np.dot(invC, h1)
        r2 = _lambda*np.dot(invC, h2)
        r3 = np.cross(r1, r2)
        t = _lambda*np.dot(invC, h3)
        #pdb.set_trace()

    def track(self):
        # this is a dumb tracking to use as baseline
        m_c_i = self.detected_kp_img[self.kp_of_marker[self.marker_c]]
        m_f_i = self.detected_kp_img[self.kp_of_marker[self.marker_f]]
        cf_i = m_f_i - m_c_i
        yaw = math.atan2(cf_i[1], cf_i[0])
        self.cam_to_irm_T = tf.transformations.euler_matrix(math.pi, 0, yaw, 'sxyz')#np.eye(4)
        m_c_c = np.dot(self.invK, utils.to_homo(m_c_i))
        self.cam_to_irm_T[:3,3] = m_c_c*1.35
        self.cam_to_body_T = np.dot(self.irm_to_body_T, self.cam_to_irm_T)
        self.world_to_irm_T = np.dot(self.cam_to_irm_T, self.world_to_cam_T)

        

    def project(self, body_to_world_T):
        self.markers_world = np.array([np.dot(body_to_world_T, m_b) for m_b in self.markers_body])
        self.projected_markers_img = cv2.projectPoints(np.array([self.markers_world[:,:3]]),
                                                       self.world_to_cam_r, np.array(self.world_to_cam_t), self.K, self.D)[0].squeeze()    
        



    def draw_debug_on_image(self, img, draw_kp_id=True):
        img_with_keypoints = cv2.drawKeypoints(img, self.keypoints, np.array([]), (0,255,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        if  draw_kp_id and self.keypoints_detected() and self.keypoints_identified():
            for i in range(len(self.keypoints)):
                cv2.putText(img_with_keypoints, self.markers_names[self.marker_of_kp[i]],
                            round_pt(self.keypoints[i].pt), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
        return img_with_keypoints