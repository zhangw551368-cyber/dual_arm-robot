#!/usr/bin/env python3

import math
import threading

import rospy
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import DeleteModel, SetModelState, SpawnModel
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


TRAY_MODEL_NAME = "dual_ur3_tray"

LEFT_JOINTS = [
    "left_arm_shoulder_pan_joint",
    "left_arm_shoulder_lift_joint",
    "left_arm_elbow_joint",
    "left_arm_wrist_1_joint",
    "left_arm_wrist_2_joint",
    "left_arm_wrist_3_joint",
]
RIGHT_JOINTS = [
    "right_arm_shoulder_pan_joint",
    "right_arm_shoulder_lift_joint",
    "right_arm_elbow_joint",
    "right_arm_wrist_1_joint",
    "right_arm_wrist_2_joint",
    "right_arm_wrist_3_joint",
]

POSES = {
    "home": {
        "left": [1.2, -1.0, 1.4, -1.4, -1.57, 0.0],
        "right": [-1.2, -1.0, 1.4, -1.4, 1.57, 0.0],
    },
    "support": {
        "left": [0.7, -1.2, 1.6, -1.6, -1.57, 0.0],
        "right": [-0.7, -1.2, 1.6, -1.6, 1.57, 0.0],
    },
    "carry": {
        "left": [1.4, -1.4, 1.6, -1.7, -1.57, 0.15],
        "right": [-1.4, -1.4, 1.6, -1.7, 1.57, -0.15],
    },
}

TRAY_POSES = {
    "home": (0.34, 0.0, 0.46),
    "support": (0.38, 0.0, 0.58),
    "carry": (0.52, 0.0, 0.64),
}


def tray_sdf():
    return """<?xml version="1.0"?>
<sdf version="1.6">
  <model name="dual_ur3_tray">
    <static>true</static>
    <link name="tray_link">
      <visual name="tray_visual">
        <geometry>
          <box><size>0.42 0.18 0.025</size></box>
        </geometry>
        <material>
          <ambient>0.05 0.28 0.95 1</ambient>
          <diffuse>0.05 0.28 0.95 1</diffuse>
        </material>
      </visual>
      <collision name="tray_collision">
        <geometry>
          <box><size>0.42 0.18 0.025</size></box>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
"""


def make_model_state(x, y, z):
    state = ModelState()
    state.model_name = TRAY_MODEL_NAME
    state.reference_frame = "world"
    state.pose.position.x = x
    state.pose.position.y = y
    state.pose.position.z = z
    state.pose.orientation.w = 1.0
    return state


def spawn_tray():
    rospy.wait_for_service("/gazebo/spawn_sdf_model")
    rospy.wait_for_service("/gazebo/delete_model")
    spawn_model = rospy.ServiceProxy("/gazebo/spawn_sdf_model", SpawnModel)
    delete_model = rospy.ServiceProxy("/gazebo/delete_model", DeleteModel)

    try:
        delete_model(TRAY_MODEL_NAME)
    except rospy.ServiceException:
        pass

    x, y, z = TRAY_POSES["home"]
    pose = make_model_state(x, y, z).pose
    spawn_model(TRAY_MODEL_NAME, tray_sdf(), "", pose, "world")
    rospy.loginfo("Spawned Gazebo tray model '%s'", TRAY_MODEL_NAME)


def interpolate_tray(set_state, start_xyz, end_xyz, duration):
    rate = rospy.Rate(30)
    start_time = rospy.Time.now()
    while not rospy.is_shutdown():
        elapsed = (rospy.Time.now() - start_time).to_sec()
        alpha = min(1.0, elapsed / max(duration, 0.1))
        smooth = 0.5 - 0.5 * math.cos(math.pi * alpha)
        xyz = tuple(s + (e - s) * smooth for s, e in zip(start_xyz, end_xyz))
        try:
            set_state(make_model_state(*xyz))
        except rospy.ServiceException as exc:
            rospy.logwarn("Failed to update tray pose: %s", exc)
        if alpha >= 1.0:
            break
        rate.sleep()


def make_trajectory(joint_names, positions, duration):
    trajectory = JointTrajectory()
    trajectory.joint_names = joint_names
    point = JointTrajectoryPoint()
    point.positions = positions
    point.velocities = [0.0] * len(positions)
    point.time_from_start = rospy.Duration(duration)
    trajectory.points = [point]
    return trajectory


def wait_for_subscribers(pub, topic):
    while not rospy.is_shutdown() and pub.get_num_connections() == 0:
        rospy.loginfo("Waiting for subscriber on %s", topic)
        rospy.sleep(0.1)


def command_pose(left_pub, right_pub, set_state, current_tray_pose, pose_name, duration):
    rospy.loginfo("Commanding tray demo pose: %s", pose_name)
    target_tray_pose = TRAY_POSES[pose_name]
    tray_thread = threading.Thread(
        target=interpolate_tray,
        args=(set_state, current_tray_pose, target_tray_pose, duration),
    )
    tray_thread.daemon = True
    tray_thread.start()

    left_pub.publish(make_trajectory(LEFT_JOINTS, POSES[pose_name]["left"], duration))
    right_pub.publish(make_trajectory(RIGHT_JOINTS, POSES[pose_name]["right"], duration))
    tray_thread.join()
    rospy.sleep(0.5)
    return target_tray_pose


def main():
    rospy.init_node("carry_tray_demo", anonymous=True)

    spawn_tray()
    rospy.wait_for_service("/gazebo/set_model_state")
    set_state = rospy.ServiceProxy("/gazebo/set_model_state", SetModelState)

    left_pub = rospy.Publisher(
        "/left_arm_joint_traj_controller/command", JointTrajectory, queue_size=1
    )
    right_pub = rospy.Publisher(
        "/right_arm_joint_traj_controller/command", JointTrajectory, queue_size=1
    )
    wait_for_subscribers(left_pub, "/left_arm_joint_traj_controller/command")
    wait_for_subscribers(right_pub, "/right_arm_joint_traj_controller/command")

    current_tray_pose = TRAY_POSES["home"]
    for pose_name in ["home", "support", "carry", "support", "home"]:
        current_tray_pose = command_pose(
            left_pub, right_pub, set_state, current_tray_pose, pose_name, 3.0
        )

    rospy.loginfo("Carry tray demo finished")


if __name__ == "__main__":
    main()
