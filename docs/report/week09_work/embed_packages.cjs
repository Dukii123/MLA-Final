const fs=require('fs'),path=require('path'),CFB=require('./cfb.js');
function u32(n){let b=Buffer.alloc(4);b.writeUInt32LE(n);return b;}
function u16(n){let b=Buffer.alloc(2);b.writeUInt16LE(n);return b;}
function str(s){return Buffer.from(s+'\0','ascii');}
for(const [source,out] of [['000010011.WAV','audio.bin'],['../Group05_Week09_Attachments.zip','evidence.bin']]){
 const file=path.basename(source),data=fs.readFileSync(path.join(__dirname,source)),name=str(file);
 const body=Buffer.concat([u16(2),name,name,u16(0),u16(3),u32(name.length),name,u32(data.length),data]);
 const native=Buffer.concat([u32(body.length),body]);
 const cfb=CFB.utils.cfb_new({CLSID:'0c00030000000000c000000000000046'});
 CFB.utils.cfb_add(cfb,'\x01Ole10Native',native);
 CFB.utils.cfb_add(cfb,'\x01CompObj',Buffer.from('0100feff030a0000ffffffff0c00030000000000c000000000000046080000005061636b61676500080000005061636b6167650000000000f439b271000000000000000000000000','hex'));
 CFB.utils.cfb_add(cfb,'\x01Ole',Buffer.from('0100000200000000000000000000000000000000','hex'));
 const buf=CFB.write(cfb,{type:'buffer'});fs.writeFileSync(path.join(__dirname,out),buf);
 const read=CFB.read(buf,{type:'buffer'});const n=Buffer.from(CFB.find(read,'\x01Ole10Native').content);
 if(!n.subarray(n.length-data.length).equals(data))throw new Error('Payload mismatch');
 console.log(file, data.length,'bytes embedded and verified');
}
