-- trivial protocol example
-- declare our protocol
gotthard_proto = Proto("gotthard_proto","Gotthard Protocol")
local f_udp_dstport = Field.new("udp.dstport")
-- create a function to dissect it
function gotthard_proto.dissector(buffer,pinfo,tree)
    --if f_udp_dstport() and f_udp_dstport().value == 9999 then
    if buffer(0,1):bitfield(0,1) == 0 then
        pinfo.cols.protocol = "Gotthard Request"
        local subtree = tree:add(gotthard_proto,buffer(),"Gotthard Request")
        subtree:add(buffer(0,1),"updated: " .. buffer(0,1):bitfield(1,1))
        subtree:add(buffer(0,1),"from_switch: " .. buffer(0,1):bitfield(2,1))
        subtree:add(buffer(1,4),"cl_id: " .. buffer(1,4):uint())
        subtree:add(buffer(5,4),"req_id: " .. buffer(5,4):uint())
        subtree:add(buffer(9,4),"r_key: " .. buffer(9,4):uint())
        subtree:add(buffer(13,4),"w_key: " .. buffer(13,4):uint())
        subtree:add(buffer(17,100),"r_value: " .. buffer(17,100))
        subtree:add(buffer(117,100),"w_value: " .. buffer(117,100))
    else
        pinfo.cols.protocol = "Gotthard Response"
        local subtree = tree:add(gotthard_proto,buffer(),"Gotthard Response")
        subtree:add(buffer(0,1),"updated: " .. buffer(0,1):bitfield(1,1))
        subtree:add(buffer(0,1),"from_switch: " .. buffer(0,1):bitfield(2,1))
        subtree:add(buffer(1,4),"cl_id: " .. buffer(1,4):uint())
        subtree:add(buffer(5,4),"req_id: " .. buffer(5,4):uint())
        subtree:add(buffer(9,1),"status: " .. buffer(9,1):uint())
        subtree:add(buffer(10,4),"key: " .. buffer(10,4):uint())
        subtree:add(buffer(14,100),"value: " .. buffer(14,100))
    end
end
-- load the udp.port table
udp_dst_table = DissectorTable.get("udp.port")
udp_dst_table:add(9999,gotthard_proto)
