for j in FMA ADD MUL;
do 
	for i in HALF SINGLE DOUBLE;
	do
		make TYPE=$j PRECISION=$i DEBUG=1 OPS=100 clean
		make TYPE=$j PRECISION=$i DEBUG=1 OPS=100 generate
		make TYPE=$j PRECISION=$i DEBUG=1 OPS=100 test
	done;

done;

exit 0
