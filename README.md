# smocap
Simple ROS mocap node

Uses ceiling mounted cameras to detect and localize active infrared markers.


<table>
  <tr>
  <td><img src="https://lh4.googleusercontent.com/Krs0lGRR-d27itPQVsvEPa2Y8CNcFzQyiw5EC-Wtf49iDOlMmXB-KBIYJGIUjqpqTskmwMb3jtMZOfQllg9a9MTqbuG-0_z8wcmCDFEqZ-3Tcr5TFOi0-G1rV7gV_cErPMQXAAJG" alt="Ceiling mounted camera" width="304" /></td>
  </tr>
  <tr>
	<td>Ceiling mounted camera</td> 
  </tr>
  </table>

<a href="https://www.youtube.com/watch?v=rcXm4QCaq64">video 1</a>
<a href="https://www.youtube.com/watch?v=X8M0IHWhTcs">video 2</a>
<a href="https://www.youtube.com/watch?v=_u4qhHbuV6Q">video 3</a>
<a href="https://youtu.be/LCjn09UPtN0">video 4</a>

## Running in simulation

 * **roslaunch smocap_gazebo gazebo_hog_marker.launch**
 will start gazebo and load a single **hand of god** (that is a remotely controlled solid) infrared marker.
 
 * **roslaunch smocap_gazebo smocap_single_cam.launch**
 will load a camera in gazebo and start the smocap node
 
 * **rviz -d **
 
## Running real setup

 * have a fixed camera output an image topic in ROS
 








#### 

 * starting gazebo spawning an hog aruco marker:
   **  roslaunch smocap_gazebo gazebo_hog_marker.launch marker_urdf:=hog_chessboard.urdf.xacro marker_texture:=Aruco0  **
 * spawning a single fixed camera in gazebo:
   ** roslaunch smocap_gazebo  single_cam.launch pos_x:=0. pos_y:=0. pos_z:=3. rot_P:=1.5707963267948966 **
 *
