#!/usr/bin/env python3

import argparse

import rospy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


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
        "left": [0.8, -1.0, 1.3, -1.4, -1.57, 0.0],
        "right": [-0.8, -1.0, 1.3, -1.4, 1.57, 0.0],
    },
    "ready": {
        "left": [1.2, -1.0, 1.4, -1.4, -1.57, 0.0],
        "right": [-1.2, -1.0, 1.4, -1.4, 1.57, 0.0],
    },
    "folded": {
        "left": [1.4, -1.4, 1.6, -1.7, -1.57, 0.15],
        "right": [-1.4, -1.4, 1.6, -1.7, 1.57, -0.15],
    },
}


def make_msg(joint_names, positions, duration):
    msg = JointTrajectory()
    msg.joint_names = joint_names
    point = JointTrajectoryPoint()
    point.positions = positions
    point.velocities = [0.0] * len(positions)
    point.time_from_start = rospy.Duration(duration)
    msg.points.append(point)
    return msg


def wait_for_subscribers(pub, name):
    rate = rospy.Rate(10)
    while pub.get_num_connections() == 0 and not rospy.is_shutdown():
        rospy.loginfo("Waiting for subscriber on %s", name)
        rate.sleep()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pose", choices=sorted(POSES), default="home")
    parser.add_argument("--duration", type=float, default=4.0)
    args = parser.parse_args(rospy.myargv()[1:])

    rospy.init_node("send_ur3_dual_pose")
    left_pub = rospy.Publisher(
        "/left_arm_joint_traj_controller/command", JointTrajectory, queue_size=1
    )
    right_pub = rospy.Publisher(
        "/right_arm_joint_traj_controller/command", JointTrajectory, queue_size=1
    )

    wait_for_subscribers(left_pub, "/left_arm_joint_traj_controller/command")
    wait_for_subscribers(right_pub, "/right_arm_joint_traj_controller/command")

    pose = POSES[args.pose]
    left_pub.publish(make_msg(LEFT_JOINTS, pose["left"], args.duration))
    right_pub.publish(make_msg(RIGHT_JOINTS, pose["right"], args.duration))
    rospy.loginfo("Sent %s pose to both UR3 arms", args.pose)
    rospy.sleep(0.5)


if __name__ == "__main__":
    main()
