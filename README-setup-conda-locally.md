 
 # For installing conda env locally 
 ```
 # Use e.g. the Anaconda PowerShell
 cd <to\folder>
 conda env create --prefix .\.conda -f .\environment.yaml
 ```

 # For activating conda env
```
# Use e.g. the Anaconda PowerShell
cd <to\folder>
conda config --set env_prompt '({name})'
conda activate .\.conda
```

# For deactivating conda env
```
# Use e.g. the Anaconda PowerShell
conda config --set env_prompt '({default_env})'
conda deactivate
conda activate base
```

# For updating conda env locally
 ```
 # Use e.g. the Anaconda PowerShell
 cd <to\folder>
 conda env update --prefix .\.conda -f .\environment.yaml
 ```