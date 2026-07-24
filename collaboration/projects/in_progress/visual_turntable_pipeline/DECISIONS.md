# Decisions

1. **Use candidate pooling rather than deterministic single-shot generation.**  
   The image model is stochastic. Multiple candidates per requested angle are more dependable than attempting to force exact compliance in one pass.

2. **Use parallel absolute-angle prompts as the primary method.**  
   This method produced the best complete coverage. Sequential approaches accumulated drift and duplicated views.

3. **Generate opaque images first and remove the background afterward.**  
   Qwen-generated backgrounds were inconsistent and not transparent. BiRefNet produced true alpha transparency with good edge preservation.

4. **Keep this project active, not parked.**  
   Core feasibility has been demonstrated, but canon validation and final resident calibration remain incomplete.

5. **Treat the current character as a temporary canon test fixture.**  
   The character may validate pipeline health but must not be mistaken for final Evelyn.
