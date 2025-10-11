import asyncio
import sys
import json
import os
import logging
from pathlib import Path

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# 将项目根路径加入 sys.path，便于模块导入
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def _print_validation_summary(validation_result):
    """格式化打印验证结果摘要"""
    print(f"📊 验证状态: {validation_result.get('validation_status', 'unknown')}")
    print(f"📈 代码覆盖率: {validation_result.get('coverage', 0)}%")
    print(f"🔄 回归检测: {'是' if validation_result.get('regression_detected', False) else '否'}")
    
    # AI生成测试信息
    ai_info = validation_result.get('ai_generated_test')
    if ai_info:
        print(f"🤖 AI生成测试: ✅ 成功")
        print(f"   📝 测试文件: {ai_info.get('file_path', 'unknown')}")
    else:
        print(f"🤖 AI生成测试: ⏭️ 未使用")
    
    # 测试结果详情
    test_results = validation_result.get('test_results', {})
    
    # 单元测试结果
    unit_results = test_results.get('unit', {})
    if unit_results:
        status = "✅ 通过" if unit_results.get('passed', False) else "❌ 失败"
        print(f"🧪 单元测试: {status}")
        if not unit_results.get('passed', False) and unit_results.get('stderr'):
            # 格式化错误输出
            stderr = unit_results['stderr']
            # 移除转义字符并格式化
            stderr_clean = stderr.replace('\\r\\n', '\n').replace('\\n', '\n').replace('\\r', '\n')
            print("   📝 错误详情:")
            for line in stderr_clean.split('\n')[:10]:  # 只显示前10行
                if line.strip():
                    print(f"      {line.strip()}")
    
    # 集成测试结果
    integration_results = test_results.get('integration', {})
    if integration_results:
        if integration_results.get('skipped', False):
            print(f"🔗 集成测试: ⏭️ 跳过 ({integration_results.get('message', '')})")
        else:
            status = "✅ 通过" if integration_results.get('passed', False) else "❌ 失败"
            print(f"🔗 集成测试: {status}")
    
    # 性能测试结果
    performance_metrics = validation_result.get('performance_metrics', {})
    if performance_metrics and performance_metrics.get('metrics'):
        print(f"⚡ 性能测试: ✅ 通过")
        metrics = performance_metrics['metrics']
        for key, value in metrics.items():
            print(f"   📊 {key}: {value}")
    
    print()  # 空行分隔


from coordinator.coordinator import Coordinator  # noqa: E402
from agents.bug_detection_agent.agent import BugDetectionAgent  # noqa: E402
from agents.fix_execution_agent.agent import FixExecutionAgent  # noqa: E402
from agents.test_validation_agent.agent import TestValidationAgent  # noqa: E402
from config.settings import settings  # noqa: E402


async def main():
    # 0) 启用所需检测工具（配置层）：开启 pylint/flake8，关闭 static_detector
    try:
        if not hasattr(settings, 'TOOLS'):
            settings.TOOLS = {}
        settings.TOOLS.setdefault('pylint', {})['enabled'] = True
        settings.TOOLS.setdefault('flake8', {})['enabled'] = True
        settings.TOOLS.setdefault('static_detector', {})['enabled'] = False
    except Exception:
        pass

    # 配置信息 - 优先使用现有DeepSeek配置
    try:
        from api.deepseek_config import deepseek_config
        ai_api_key = deepseek_config.api_key if deepseek_config.is_configured() else os.getenv("DEEPSEEK_API_KEY")
        print(f"🔑 使用DeepSeek API密钥: {ai_api_key[:10]}...{ai_api_key[-10:] if ai_api_key else 'None'}")
    except ImportError:
        ai_api_key = os.getenv("DEEPSEEK_API_KEY")
        print(f"🔑 使用环境变量API密钥: {ai_api_key[:10]}...{ai_api_key[-10:] if ai_api_key else 'None'}")
    
    config = {
        "ai_api_key": ai_api_key,  # AI API密钥
        "min_coverage": 80,  # 最小代码覆盖率
        "test_options": {
            "generate_with_ai": True,  # 启用AI测试生成
            "cleanup_ai_tests": False  # 保留AI生成的文件用于查看
        }
    }

    # 1) 启动协调中心
    print("\n================= COORDINATOR BOOT =================")
    coordinator = Coordinator(config=config)
    await coordinator.start()
    print("✅ Coordinator 已启动")

    # 2) 启动并注册需要的 Agent（完整集：检测 + 修复 + 验证）
    print("\n================= AGENTS BOOT & REGISTER ===========")
    bug_agent = BugDetectionAgent(config=config)
    await bug_agent.start()
    await coordinator.register_agent('bug_detection_agent', bug_agent)
    print("✅ BugDetectionAgent 已启动并注册")

    # 启动并注册修复执行Agent
    fix_agent = FixExecutionAgent(config=config)
    await fix_agent.start()
    await coordinator.register_agent('fix_execution_agent', fix_agent)
    print("✅ FixExecutionAgent 已启动并注册")

    # 启动并注册测试验证Agent
    test_agent = TestValidationAgent(config=config)
    await test_agent.start()
    await coordinator.register_agent('test_validation_agent', test_agent)
    print("✅ TestValidationAgent 已启动并注册")

    # 3) 选择待测文件路径（支持命令行参数和交互式输入）
    print("\n================= TEST TARGET =======================")
    # 支持命令行参数或交互式输入；若无输入，使用默认示例文件
    custom_path = None
    if len(sys.argv) > 1:
        custom_path = sys.argv[1]
    if not custom_path:
        try:
            user_input = input("请输入待检测文件路径（回车使用默认 tests/test_python_bad.py）: ").strip()
            custom_path = user_input or None
        except Exception:
            custom_path = None

    if custom_path:
        p = Path(custom_path)
        test_file = str(p if p.is_absolute() else (PROJECT_ROOT / p))
    else:
        test_file = str(CURRENT_DIR / 'test_python_bad.py')

    if not Path(test_file).exists():
        fallback = str(CURRENT_DIR / 'test_python_bad.py')
        print(f"⚠️ 指定的文件不存在，使用默认: {fallback}")
        test_file = fallback

    print(f"📄 测试文件: {test_file}")

    # 4) 创建 detect_bugs 任务并分配给 bug_detection_agent
    # 检测配置：启用所有检测工具（static/pylint/flake8/bandit/mypy/ai）
    print("\n================= DETECT TASK SUBMIT ================")
    task_payload = {
        'file_path': test_file,
        'options': {
            'enable_static': True,
            'enable_pylint': True,
            'enable_flake8': True,
            'enable_bandit': True,
            'enable_mypy': True,
            'enable_ai_analysis': True,
            'enable_dynamic': False
        }
    }
    task_id = await coordinator.create_task('detect_bugs', task_payload)
    print(f"🆔 任务已创建: {task_id}")
    await coordinator.assign_task(task_id, 'bug_detection_agent')
    print("📤 已分配到: bug_detection_agent")

    # 5) 等待检测任务完成
    print("\n================= DETECT RESULT =====================")
    detection_result = await coordinator.task_manager.get_task_result(task_id, timeout=600)
    result_ok = detection_result.get('success')
    det = detection_result.get('detection_results', {})
    issues = det.get('issues', [])
    tools = det.get('detection_tools', [])
    print(f"✅ 成功: {result_ok}")
    print(f"🛠️ 使用工具: {', '.join(tools) if tools else '无'}")
    print(f"🐞 缺陷总数: {det.get('total_issues', 0)}")
    if issues:
        print("\nAll Issues:")
        for i, issue in enumerate(issues, start=1):
            loc = f"{issue.get('file','')}:{issue.get('line',0)}:{issue.get('column',0)}"
            sev = issue.get('severity', 'info')
            typ = issue.get('type', issue.get('symbol', 'unknown'))
            msg = issue.get('message', '')
            print(f"  {i:02d}. [{sev}] {typ} @ {loc} - {msg}")
    else:
        print("（未发现问题，若为意外，请确认已安装并启用 pylint/flake8）")

    # 6) 修复与验证编排（完整流程 - 合并两个版本的功能）
    print("\n================= FIX & VALIDATION ===================")
    
    # 6.1) 创建修复任务
    fix_task_payload = {
        'file_path': test_file,
        'issues': issues,
        'decisions': {'auto_fixable': issues, 'ai_assisted': [], 'manual_review': []}
    }
    fix_task_id = await coordinator.create_task('fix_issues', fix_task_payload)
    await coordinator.assign_task(fix_task_id, 'fix_execution_agent')
    print(f"🆔 修复任务创建并分配: {fix_task_id} -> fix_execution_agent")
    
    # 6.2) 等待修复完成
    fix_result = await coordinator.task_manager.get_task_result(fix_task_id, timeout=900)
    print("🧩 修复结果摘要:")
    print({
        'success': fix_result.get('success'),
        'fixed_issues': len(fix_result.get('fix_results', [])),
        'errors': fix_result.get('errors', [])[:3]
    })
    
    # 6.3) 创建测试验证任务（完整验证流程）
    # 使用修复后的文件路径，而不是原始文件
    fixed_file_path = None
    if fix_result.get('success') and fix_result.get('fix_results'):
        # 从修复结果中获取修复后的文件路径
        for fix_item in fix_result.get('fix_results', []):
            if 'after' in fix_item:
                fixed_file_path = fix_item['after']
                break
    
    # 如果没有找到修复后的文件，使用原始文件
    test_file_for_validation = fixed_file_path if fixed_file_path else test_file
    print(f"🎯 测试验证将使用文件: {test_file_for_validation}")
    
    validation_task_payload = {
        'file_path': test_file_for_validation,
        'fix_result': fix_result,
        'test_types': ['unit', 'integration'],
        'options': {
            'generate_with_ai': True,
            'min_coverage': 70
        }
    }
    validation_task_id = await coordinator.create_task('validate_fix', validation_task_payload)
    await coordinator.assign_task(validation_task_id, 'test_validation_agent')
    print(f"🆔 验证任务创建并分配: {validation_task_id} -> test_validation_agent")
    
    # 6.4) 等待验证完成
    validation_result = await coordinator.task_manager.get_task_result(validation_task_id, timeout=600)
    print("✅ 验证结果摘要:")
    _print_validation_summary(validation_result)

    # 7) 收尾
    print("\n================= SHUTDOWN ===========================")
    await coordinator.stop()
    await bug_agent.stop()
    await fix_agent.stop()
    await test_agent.stop()
    print("✅ 已退出")


if __name__ == '__main__':
    asyncio.run(main())


