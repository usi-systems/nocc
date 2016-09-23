-- trivial protocol example
-- declare our protocol
gotthard_proto = Proto("gotthard_proto","Gotthard Protocol")
local f_udp_dstport = Field.new("udp.dstport")
-- create a function to dissect it
function gotthard_proto.dissector(buffer,pinfo,tree)
    --if f_udp_dstport() and f_udp_dstport().value == 9999 then
    local opNames = {'READ', 'WRITE', 'VALUE', 'UPDATED'}
    local msgType = buffer(0,1):bitfield(0,1) == 0 and "Request" or "Response"
    pinfo.cols.protocol = "Gotthard " .. msgType
    local subtree = tree:add(gotthard_proto,buffer(),"Gotthard " .. msgType)
    subtree:add(buffer(0,1),"from_switch: " .. buffer(0,1):bitfield(1,1))
    subtree:add(buffer(1,4),"cl_id: " .. buffer(1,4):uint())
    subtree:add(buffer(5,4),"req_id: " .. buffer(5,4):uint())
    subtree:add(buffer(9,1),"status: " .. buffer(9,1):uint())
    local op_cnt = buffer(10,1):uint()
    subtree:add(buffer(10,1),"op_cnt: " .. op_cnt)
    print "start"
    for i = 0, op_cnt-1 do
        local op_type = buffer(11+(i*105),1):uint()
        print(i .. " and " .. 11+(i*105))
        subtree:add(buffer(11+(i*105),1),"op_type: " .. opNames[op_type+1])
        subtree:add(buffer(11+(i*105)+1,4),"op_key: " .. buffer(11+(i*105)+1,4):uint())
        subtree:add(buffer(11+(i*105)+5,100),"op_val: " .. buffer(11+(i*105)+5,100))

    end
end
-- load the udp.port table
udp_dst_table = DissectorTable.get("udp.port")
udp_dst_table:add(9999,gotthard_proto)
