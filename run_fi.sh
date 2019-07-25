#!/bin/bash


set -x
set -e

FAULTNUM=1000

#THRESHOLD CHECKBLOCK, 4.89887409882427959928e-06, 0
#THRESHOLD CHECKBLOCK, 1.07916062308532900715e-07, 1
#THRESHOLD CHECKBLOCK, 5.52291090416545671360e-07, 10

do_micros_fmanot_biased(){
    
    for conf in fmanotbiased; # mul;
    do
        for siz in 0 1 10;
        do
            rm -rf *.csv logs/* /var/radiation-benchmarks/log/2019_*

            cd codes/micro_mp_hard/
            make clean
	    zero=4.89887409882427959928e-06
            if [ ${siz} -eq 1 ];
	    then
		zero=1.07916062308532900715e-07
	    fi

            if [ ${siz} -eq 10 ];
	    then
		zero=5.52291090416545671360e-07
	    fi


            make CHECKBLOCK=${siz} ZERO_FLOAT=${zero}
            cd ../../
            ./app_profiler.py -c codes/micro_mp_hard/double_dmrmixed_micro_${conf}.conf 
            ./fault_injector.py -i ${FAULTNUM} -c codes/micro_mp_hard/double_dmrmixed_micro_${conf}.conf 
            
            tar czf fi_micro_${conf}_dmrmixed_double_single_bit_${siz}.tar.gz fi_micro_${conf}_dmrmixed_double_single_bit.csv /var/radiation-benchmarks/log/
        done
    done 
}

#THRESHOLD CHECKBLOCK, 1.40383856286661057311e-02, 0
#THRESHOLD CHECKBLOCK, 7.87839344873475511122e-08, 1
#THRESHOLD CHECKBLOCK, 1.97272483370980467043e-06, 100
#THRESHOLD CHECKBLOCK, 1.92442706004047892066e-05, 1000


do_micros_mulnot_biased(){
    
    for conf in mulnotbiased; # mul;
    do
        for siz in 0 1 100 1000;
        do
            rm -rf *.csv logs/* /var/radiation-benchmarks/log/2019_*

            cd codes/micro_mp_hard/
            make clean
	    zero=1.5e-02
            if [ ${siz} -eq 1 ];
	    then
		zero=7.87839344873475511122e-08
	    fi

            if [ ${siz} -eq 100 ];
	    then
		zero=1.97272483370980467043e-06
	    fi

            if [ ${siz} -eq 1000 ];
	    then
		zero=1.92442706004047892066e-05
	    fi


            make CHECKBLOCK=${siz} ZERO_FLOAT=${zero}
            cd ../../

            /home/carol/carol-fi/app_profiler.py -c codes/micro_mp_hard/double_dmrmixed_micro_${conf}.conf 
            /home/carol/carol-fi/fault_injector.py -i ${FAULTNUM} -c codes/micro_mp_hard/double_dmrmixed_micro_${conf}.conf 

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
#do_hotspot
do_micros_mulnot_biased
#do_micros_fmanot_biased


rm -rf *.csv logs/* /var/radiation-benchmarks/log/2019_*

