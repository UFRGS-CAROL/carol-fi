for i in HALF SINGLE DOUBLE;
do
	make PRECISION=$i DEBUG=1 clean
	make PRECISION=$i DEBUG=1 generate
	make PRECISION=$i DEBUG=1 test


done;

exit 0
