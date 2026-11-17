const fs=require('fs'),CFB=require('../week11_work/cfb.js');
// Mô phỏng đúng hành vi Word khi nháy đúp OLE Package: đọc CFB, lấy stream Ole10Native, giải payload zip
// Layout body (như embed_packages.cjs): [u16 2][name][name][u16 0][u16 3][u32 L][name][u32 datalen][data]
const bin = fs.readFileSync(process.argv[2]);
const cfb = CFB.read(bin, {type:'buffer'});
const entry = CFB.find(cfb, '\x01Ole10Native');
if (!entry) throw new Error('KHONG thay stream Ole10Native');
const n = Buffer.from(entry.content);
const total = n.readUInt32LE(0);
const body = n.subarray(4, 4 + total);
const L = body.indexOf(0, 2) - 1;       // tên kết thúc bằng \0: vị trí zero đầu tiên (>=2) trừ offset 2, +1
const dataLen = body.readUInt32LE(10 + 3 * L);
const data = body.subarray(14 + 3 * L, 14 + 3 * L + dataLen);
if (data.length !== dataLen) throw new Error('payload doc khong du chieu dai');
fs.writeFileSync(process.argv[3], data);
console.log('OLE OK: payload =', dataLen, 'bytes ->', process.argv[3]);
