 
 # For installing conda env locally
 ```
 cd <to\folder>
 conda env create --prefix .\.conda -f .\environment.yaml
 ```

 # For activating conda env
```
cd <to\folder>
conda config --set env_prompt '({name})'
conda activate .\.conda
```

# For deactivating conda env
```
conda config --set env_prompt '({default_env})'
conda deactivate
conda activate base
```

# For updating conda env locally
 ```
 cd <to\folder>
 conda env update --prefix .\.conda -f .\environment.yaml
 ```