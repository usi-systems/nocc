-- trivial protocol example
-- declare our protocol
gotthard_proto = Proto("gotthard_proto","Gotthard Protocol")
local f_udp_dstport = Field.new("udp.dstport")
-- create a function to dissect it
function gotthard_proto.dissector(buffer,pinfo,tree)
    if f_udp_dstport() and f_udp_dstport().value == 9999 then
        pinfo.cols.protocol = "Gotthard Request"
        local subtree = tree:add(gotthard_proto,buffer(),"Gotthard Request")
        subtree:add(buffer(0,1),"flags: " .. buffer(0,1):uint())
        subtree:add(buffer(1,4),"cl_id: " .. buffer(1,4):uint())
        subtree:add(buffer(5,4),"req_id: " .. buffer(5,4):uint())
        subtree:add(buffer(9,4),"r_key: " .. buffer(9,4):uint())
        subtree:add(buffer(13,4),"r_version: " .. buffer(13,4):uint())
        subtree:add(buffer(17,4),"w_key: " .. buffer(17,4):uint())
        subtree:add(buffer(21,100),"value: " .. buffer(21,100))
    else
        pinfo.cols.protocol = "Gotthard Response"
        local subtree = tree:add(gotthard_proto,buffer(),"Gotthard Response")
        subtree:add(buffer(0,1),"flags: " .. buffer(0,1):uint())
        subtree:add(buffer(1,4),"cl_id: " .. buffer(1,4):uint())
        subtree:add(buffer(5,4),"req_id: " .. buffer(5,4):uint())
        subtree:add(buffer(9,1),"status: " .. buffer(9,1):uint())
        subtree:add(buffer(10,4),"key: " .. buffer(10,4):uint())
        subtree:add(buffer(14,4),"version: " .. buffer(14,4):uint())
        subtree:add(buffer(18,100),"value: " .. buffer(18,100))
    end
end
-- load the udp.port table
udp_dst_table = DissectorTable.get("udp.port")
udp_dst_table:add(9999,gotthard_proto)
