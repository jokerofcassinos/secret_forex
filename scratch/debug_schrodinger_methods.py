import schrodinger_engine
print(dir(schrodinger_engine.QuantumCloudSolver))
solver = schrodinger_engine.QuantumCloudSolver(512, 0.1)
print(f"Has shift_grid: {hasattr(solver, 'shift_grid')}")
