# Dual Arm Robot Workspace

这是 `/home/xiaoai/gzu_ws` 的双臂 UR3 ROS Noetic 工作区，包含双 UR3 模型、Gazebo 仿真、MoveIt 配置、UR 实机驱动、Robotiq 夹爪包和手眼标定相关包。

## 快速启动

每个新终端先进入工作区并加载环境：

```bash
cd /home/xiaoai/gzu_ws
source /opt/ros/noetic/setup.bash
source devel/setup.bash
```

如果当前终端启用了 conda，可以先执行 `command -v conda >/dev/null 2>&1 && conda deactivate || true`，避免 conda 的 Qt/Python 库影响 RViz、MoveIt。

## 常用入口

| 目标 | 命令 |
| --- | --- |
| RViz 只看双臂模型 | `roslaunch ur_description view_ur3_dual.launch` |
| Gazebo 只看双臂本体 | `roslaunch ur_description ur3_dual_gazebo.launch` |
| MoveIt 假执行规划 | `roslaunch ur3_dual_moveit_config demo.launch` |
| Gazebo + MoveIt 联合仿真 | `LIBGL_ALWAYS_SOFTWARE=1 roslaunch ur3_dual_moveit_config demo_gazebo.launch` |
| 双臂 MoveIt 脚本 demo | `rosrun ur3_dual_moveit_config plan_both_arms_demo.py` |
| Gazebo 关节控制脚本 | `rosrun ur_description send_ur3_dual_pose.py --pose home --duration 4` |
| 双 UR3 实机驱动 | `roslaunch ur_robot_driver ur3_dual_bringup.launch` |

## 关键目录

| 路径 | 作用 |
| --- | --- |
| `src/ur_description` | URDF/Xacro、模型、Gazebo 单独启动入口 |
| `src/ur3_dual_moveit_config` | 双 UR3 MoveIt、RViz、Gazebo+MoveIt 联合仿真 |
| `src/ur_robot_driver` | UR 真实机械臂驱动和控制器配置 |
| `src/robotiq` | Robotiq 夹爪、Modbus、Gazebo 插件 |
| `src/moveit_calibration` | MoveIt 手眼标定插件 |

## 控制器说明

Gazebo 联合仿真会显式把 MoveIt 连接到下面两个 Gazebo action controller：

```text
left_arm_joint_traj_controller
right_arm_joint_traj_controller
```

真实双 UR3 使用左右命名空间下的 UR scaled controller：

```text
/left_arm/scaled_pos_joint_traj_controller
/right_arm/scaled_pos_joint_traj_controller
```

因此：

1. 仿真优先用 `roslaunch ur3_dual_moveit_config demo_gazebo.launch`。
2. 实机 MoveIt 使用 `move_group.launch` + `moveit_rviz.launch`，控制器映射在 `src/ur3_dual_moveit_config/config/ur3_dual_controllers_moveit.yaml`。
3. RViz 里 `Plan` 只是规划预览，只有点击 `Execute` 或 `Plan & Execute` 才会把轨迹发给 Gazebo/真实控制器。

## 文档

| 文档 | 用途 |
| --- | --- |
| `双臂UR3仿真启动指南.md` | 仿真、RViz、Gazebo、MoveIt 排错和练习路线 |
| `双臂UR3机器人使用手册2026年-整理版.md` | 真实双臂、夹爪、UR16e、视觉相关总手册 |
| `初学者实机抓取与双臂装配路线.md` | 从单臂实机到双臂装配的学习路线 |

## Git 说明

`.gitignore` 已忽略 `build/`、`devel/`、`.vscode/`、`.catkin_workspace` 等本机生成内容。拉取仓库后需要在目标机器重新编译：

```bash
cd /home/xiaoai/gzu_ws
catkin_make
source devel/setup.bash
```
