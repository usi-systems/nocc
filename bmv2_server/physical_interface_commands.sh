able_set_default send_frame _drop
table_set_default forward _drop
table_set_default ipv4_lpm _drop
table_set_default t_store_update _nop
table_set_default t_req_pass1 _nop
table_set_default t_req_fix _nop
table_set_default t_opti_update _nop
table_add t_reply_client do_reply_ok 0 =>
table_add t_reply_client do_reply_abort 1 =>
table_add t_store_update do_store_update0 1 =>
table_add t_req_pass1 do_check_op0 1 => 0
table_add t_req_fix do_req_fix0 1 =>
table_add t_store_update do_store_update1 2 =>
table_add t_req_pass1 do_check_op1 2 => 0
table_add t_req_fix do_req_fix1 2 =>
table_add t_store_update do_store_update2 3 =>
table_add t_req_pass1 do_check_op2 3 => 0
table_add t_req_fix do_req_fix2 3 =>
table_add t_store_update do_store_update3 4 =>
table_add t_req_pass1 do_check_op3 4 => 0
table_add t_req_fix do_req_fix3 4 =>
table_add t_store_update do_store_update4 5 =>
table_add t_req_pass1 do_check_op4 5 => 0
table_add t_req_fix do_req_fix4 5 =>
table_add t_store_update do_store_update5 6 =>
table_add t_req_pass1 do_check_op5 6 => 0
table_add t_req_fix do_req_fix5 6 =>
table_add t_store_update do_store_update6 7 =>
table_add t_req_pass1 do_check_op6 7 => 0
table_add t_req_fix do_req_fix6 7 =>
table_add t_store_update do_store_update7 8 =>
table_add t_req_pass1 do_check_op7 8 => 0
table_add t_req_fix do_req_fix7 8 =>
table_add t_store_update do_store_update8 9 =>
table_add t_req_pass1 do_check_op8 9 => 0
table_add t_req_fix do_req_fix8 9 =>
table_add t_store_update do_store_update9 10 =>
table_add t_req_pass1 do_check_op9 10 => 0
table_add t_req_fix do_req_fix9 10 =>
table_add t_opti_update do_opti_update0 1 =>
table_add t_opti_update do_opti_update1 2 =>
table_add t_opti_update do_opti_update2 3 =>
table_add t_opti_update do_opti_update3 4 =>
table_add t_opti_update do_opti_update4 5 =>
table_add t_opti_update do_opti_update5 6 =>
table_add t_opti_update do_opti_update6 7 =>
table_add t_opti_update do_opti_update7 8 =>
table_add t_opti_update do_opti_update8 9 =>
table_add t_opti_update do_opti_update9 10 =>
table_add send_frame rewrite_mac 1 => 00:04:00:00:00:00
table_add forward set_dmac 10.0.0.10 => 00:04:00:00:00:00
table_add ipv4_lpm set_nhop 10.0.0.10/32 => 10.0.0.10 1
table_add send_frame rewrite_mac 2 => 00:04:00:00:00:01
table_add forward set_dmac 10.0.1.10 => 00:04:00:00:00:01
table_add ipv4_lpm set_nhop 10.0.1.10/32 => 10.0.1.10 2
