#!/usr/bin/env python3

import sys
import argparse

import moveit_commander
import rospy


POSES = {
    "home": {
        "left_arm_shoulder_pan_joint": 1.2,
        "left_arm_shoulder_lift_joint": -1.0,
        "left_arm_elbow_joint": 1.4,
        "left_arm_wrist_1_joint": -1.4,
        "left_arm_wrist_2_joint": -1.57,
        "left_arm_wrist_3_joint": 0.0,
        "right_arm_shoulder_pan_joint": -1.2,
        "right_arm_shoulder_lift_joint": -1.0,
        "right_arm_elbow_joint": 1.4,
        "right_arm_wrist_1_joint": -1.4,
        "right_arm_wrist_2_joint": 1.57,
        "right_arm_wrist_3_joint": 0.0,
    },
    "open": {
        "left_arm_shoulder_pan_joint": 1.2,
        "left_arm_shoulder_lift_joint": -1.0,
        "left_arm_elbow_joint": 1.4,
        "left_arm_wrist_1_joint": -1.4,
        "left_arm_wrist_2_joint": -1.57,
        "left_arm_wrist_3_joint": 0.0,
        "right_arm_shoulder_pan_joint": -1.2,
        "right_arm_shoulder_lift_joint": -1.0,
        "right_arm_elbow_joint": 1.4,
        "right_arm_wrist_1_joint": -1.4,
        "right_arm_wrist_2_joint": 1.57,
        "right_arm_wrist_3_joint": 0.0,
    },
    "assemble_ready": {
        "left_arm_shoulder_pan_joint": 1.4,
        "left_arm_shoulder_lift_joint": -1.4,
        "left_arm_elbow_joint": 1.6,
        "left_arm_wrist_1_joint": -1.7,
        "left_arm_wrist_2_joint": -1.57,
        "left_arm_wrist_3_joint": 0.15,
        "right_arm_shoulder_pan_joint": -1.4,
        "right_arm_shoulder_lift_joint": -1.4,
        "right_arm_elbow_joint": 1.6,
        "right_arm_wrist_1_joint": -1.7,
        "right_arm_wrist_2_joint": 1.57,
        "right_arm_wrist_3_joint": -0.15,
    },
}


def plan_result(plan_call_result):
    if isinstance(plan_call_result, tuple):
        success, plan, _, error_code = plan_call_result
        return bool(success), plan, error_code
    plan = plan_call_result
    success = bool(plan.joint_trajectory.points)
    return success, plan, None


def plan_and_execute(group, pose_name):
    rospy.loginfo("Planning both_arm to %s", pose_name)
    group.set_start_state_to_current_state()
    group.set_joint_value_target(POSES[pose_name])
    success, plan, error_code = plan_result(group.plan())
    if not success or not plan.joint_trajectory.points:
        rospy.logerr("Planning to %s failed. error_code=%s", pose_name, error_code)
        return False
    rospy.loginfo(
        "Plan to %s succeeded with %d trajectory points",
        pose_name,
        len(plan.joint_trajectory.points),
    )
    ok = group.execute(plan, wait=True)
    group.stop()
    group.clear_pose_targets()
    rospy.sleep(0.5)
    return ok


def main():
    parser = argparse.ArgumentParser(
        description="Plan and execute a simple both-arm MoveIt joint-space demo."
    )
    parser.add_argument(
        "--poses",
        nargs="+",
        choices=sorted(POSES),
        default=["home", "open", "assemble_ready", "home"],
        help="Pose sequence to plan and execute.",
    )
    parser.add_argument(
        "--velocity-scale",
        type=float,
        default=0.25,
        help="MoveIt max velocity scaling factor.",
    )
    parser.add_argument(
        "--acceleration-scale",
        type=float,
        default=0.25,
        help="MoveIt max acceleration scaling factor.",
    )
    args = parser.parse_args(rospy.myargv()[1:])

    moveit_commander.roscpp_initialize(sys.argv)
    rospy.init_node("plan_both_arms_demo", anonymous=True)

    group = moveit_commander.MoveGroupCommander("both_arm")
    group.set_planning_time(8.0)
    group.set_num_planning_attempts(10)
    group.set_max_velocity_scaling_factor(args.velocity_scale)
    group.set_max_acceleration_scaling_factor(args.acceleration_scale)

    rospy.loginfo("Available planning frame: %s", group.get_planning_frame())
    rospy.loginfo("Active joints: %s", group.get_active_joints())

    for pose_name in args.poses:
        if not plan_and_execute(group, pose_name):
            moveit_commander.roscpp_shutdown()
            sys.exit(1)

    rospy.loginfo("Both-arm planning demo finished")
    moveit_commander.roscpp_shutdown()


if __name__ == "__main__":
    main()
