// Arkworks compressed BN254 encoding: real Sui verification is a required gate.
export const FR=21888242871839275222246405745257275088548364400416034343698204186575808495617n;
const FQ=21888242871839275222246405745257275088696311157297823662689037894645226208583n;
export function little(n,size=32) {
  n=BigInt(n); if(n<0n || n >= (1n<<BigInt(8*size))) throw Error('INTEGER_ENCODING_RANGE');
  const a=Buffer.alloc(size); for(let i=0;i<size;i++){a[i]=Number(n&255n);n>>=8n;}return a;
}
function fq(x){x=BigInt(x);if(x<0n||x>=FQ)throw Error('NONCANONICAL_FQ');return x;}
function g1(p){
  const x=fq(p[0]),y=fq(p[1]); if (BigInt(p[2]??1)!==1n) throw Error('AFFINE_POINT_REQUIRED');
  const a=little(x); if(y>(FQ-y)%FQ)a[31]|=128; return a;
}
function g2(p){
  const x0=fq(p[0][0]),x1=fq(p[0][1]),y0=fq(p[1][0]),y1=fq(p[1][1]);
  if(p[2] && (BigInt(p[2][0])!==1n || BigInt(p[2][1])!==0n))throw Error('AFFINE_POINT_REQUIRED');
  const a=Buffer.concat([little(x0),little(x1)]),ny1=(FQ-y1)%FQ,ny0=(FQ-y0)%FQ;
  if(y1>ny1 || y1===ny1 && y0>ny0)a[63]|=128;return a;
}
export function proofBytes(p){return Buffer.concat([g1(p.pi_a),g2(p.pi_b),g1(p.pi_c)]);}
export function vkBytes(v){
  if(v.protocol!=='groth16'||v.curve!=='bn128'||v.IC.length!==v.nPublic+1)throw Error('VK_FORMAT');
  return Buffer.concat([g1(v.vk_alpha_1),g2(v.vk_beta_2),g2(v.vk_gamma_2),g2(v.vk_delta_2),little(v.IC.length,8),...v.IC.map(g1)]);
}
export function fieldBytes(values){return Buffer.concat(values.map(v=>{const n=BigInt(v);if(n<0n||n>=FR)throw Error('NONCANONICAL_FR');return little(n);}));}
