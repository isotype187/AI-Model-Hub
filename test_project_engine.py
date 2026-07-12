from core.project_engine import ProjectEngine

engine = ProjectEngine()

result = engine.write_file(
    "engine_test.py",
    'print("Project Engine test successful")'
)

print("WRITE RESULT:", result)
