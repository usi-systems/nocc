-- declare our protocol
switch2pc_proto = Proto("switch2pc_proto","switch2pc Protocol")
local f_udp_dstport = Field.new("udp.dstport")

-- create a function to dissect it
function switch2pc_proto.dissector(buffer,pinfo,tree)
    local hdrSize = 14

    local msgTypes = {'REQ', 'RES', 'PREPARE', 'VOTE', 'COMMIT', 'COMMITTED'}
    local statuses = {'OK', 'ABORT'}

    local msgType = msgTypes[buffer(0,1):uint()]
    pinfo.cols.protocol = "S2PC " .. msgType
    local subtree = tree:add(switch2pc_proto,buffer(),"S2PC " .. msgType)
    subtree:add(buffer(1,1),"status: " .. statuses[buffer(1,1):uint()])
    subtree:add(buffer(2,4),"cl_id: " .. buffer(2,4):uint())
    subtree:add(buffer(6,4),"txn_id: " .. buffer(6,4):uint())
    subtree:add(buffer(10,1),"reset: " .. buffer(10,1):uint())
    local op_cnt = buffer(11,1):uint()
    subtree:add(buffer(11,1),"op_cnt: " .. op_cnt)
    subtree:add(buffer(12,1),"participant_cnt: " .. buffer(12,1):uint())
    subtree:add(buffer(13,1),"from_switch: " .. buffer(13,1):uint())
end

-- load the udp.port table
udp_dst_table = DissectorTable.get("udp.port")
udp_dst_table:add(8000,switch2pc_proto)
udp_dst_table:add(9000,switch2pc_proto)
