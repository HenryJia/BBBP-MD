salloc --account su007-gcs --mem-per-cpu 64000 --time 48:00:00 --partition vhmem -n 64 -N 1
# ssh -o ExitOnForwardFailure=yes -f -N -R 0.0.0.0:8888:localhost:8888 henry@89.147.108.154 ;
# python -m pipenv run jupyter notebook --no-browser --ip 0.0.0.0
