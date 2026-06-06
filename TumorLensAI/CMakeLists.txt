set(MODULE_NAME TumorLensAI)

set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  TumorLensAILogic.py
  TumorLensAIMetrics.py
  TumorLensAIMONAIClient.py
  __init__.py
)

set(MODULE_PYTHON_RESOURCES
  Resources
)

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
)

