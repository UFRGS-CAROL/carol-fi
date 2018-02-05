CXX=g++ -g
CXX_FLAGS= -O3 -fopenmp -lm


SOURCES_CHECK=lulesh_check.cc lulesh-util.cc lulesh-init.cc lulesh.h ../../include/log_helper.c
SOURCES_GEN=lulesh_gen.cc lulesh-util.cc lulesh-init.cc lulesh.h 


gen_bin: $(SOURCES_GEN)
	$(CXX) $(CXX_FLAGS) $(SOURCES_GEN) -o lulesh_gen
	$(CXX) $(CXX_FLAGS) lulesh_gold_check.c lulesh-util.cc lulesh.h -o lulesh_gold_check
#	$(CXX) $(CXX_FLAGS) $(SOURCES_CHECK) -DLOGS -o lulesh_check


clean:
	rm -f lulesh_gen lulesh_check lulesh_err_inj lulesh_timing
