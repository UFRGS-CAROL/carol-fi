#!/usr/bin/env bash


# stop after first error
set -e

printf "Steps 1, 2 in \"Setting up and running CAROL-FI CUDA\" section in CAROL-FI git hub should be completed before
        proceeding further. Are these steps completed? [y/n]: "
read answer

if [ "$answer" != "y" ]; then
  printf "\nCannot proceed further\n"
	exit -1;
fi


printf "How many faults do you wish to inject?"
read inj_number

if [ "$inj_number" \< "1" ];
then
    printf "\nNumber of injections less than 1. Cannot proceed further\n"
	exit -1;
fi

printf "Where is config file?"
read config_file

if [ "$config_file" == "" ];
then
    printf "\nConfig file cannot be null\n"
	exit -1;
fi

printf "\nProfiling the application\n"
./app_profiler.py -c ${config_file}

printf "\nInjecting ", ${inj_number}, " faults on ", ${config_file}
./fault_injector.py -i ${inj_number} -c ${config_file}


for((i=0; i <= $inj_number;i++))
do
    fg
    sleep 3
done

exit 0