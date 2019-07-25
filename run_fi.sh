#!/bin/bash


set -x
set -e

FAULTNUM=1000

do_micros(){
    
    for conf in compose; #add fma mul;
    do
        for siz in 0 1 100 1000;
        do
            rm -rf *.csv logs/* /var/radiation-benchmarks/log/2019_*

            cd codes/micro_mp_hard/
            make clean
	    zero=4.4e-1
            if [ ${siz} -eq 1 ];
	    then
		zero=3e-7
	    fi
	    if [ ${siz} -eq 100 ];
	    then
		zero=6e-6
	    fi
	    if [ ${siz} -eq 1000 ];
	    then
		zero=5.8e-5
	    fi

            make CHECKBLOCK=${siz} ZERO_FLOAT=${zero}
            cd ../../
            ./app_profiler.py -c codes/micro_mp_hard/double_dmrmixed_micro_${conf}.conf 
            ./fault_injector.py -i ${FAULTNUM} -c codes/micro_mp_hard/double_dmrmixed_micro_${conf}.conf 
            
            tar czf fi_micro_${conf}_dmrmixed_double_single_bit_${siz}.tar.gz fi_micro_${conf}_dmrmixed_double_single_bit.csv /var/radiation-benchmarks/log/
        done
    done 
}

ZERO_FLOAT=2e-3
do_hotspot(){
        conf=hotspot_mp
        for siz in 0;
        do
            rm -rf *.csv logs/* /var/radiation-benchmarks/log/2019_*

            cd codes/hotspot_mp/
            make clean
			
			if [ ${siz} -gt 1 ];
			then
				ZERO_FLOAT=5e-4
			fi
			
            make CHECKBLOCK=${siz} ZERO_FLOAT=${ZERO_FLOAT}
	                
            cd ../../
            ./app_profiler.py -c codes/${conf}/double_dmrmixed_${conf}.conf 
            ./fault_injector.py -i ${FAULTNUM} -c codes/hotspot_mp/double_dmrmixed_${conf}.conf 
            
            tar czf fi_${conf}_dmrmixed_double_single_bit_${siz}.tar.gz fi_${conf}_dmrmixed_double_single_bit.csv /var/radiation-benchmarks/log/
        done
}

#do_micros
do_hotspot

rm -rf *.csv logs/* /var/radiation-benchmarks/log/2019_*

