import { useMemo, useState } from "react";
import { Code2, Copy, Download, ShieldCheck } from "lucide-react";
import "./PlatformModules.css";

function solidity(name:string,symbol:string,decimals:number,supply:string,burnable:boolean){
  const extension = burnable
    ? 'import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";\n\ncontract ' + name + 'Token is ERC20, ERC20Burnable {'
    : 'import "@openzeppelin/contracts/token/ERC20/ERC20.sol";\n\ncontract ' + name + 'Token is ERC20 {';
  return '// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\n\n' + extension +
    '\n    constructor() ERC20("' + name + '", "' + symbol + '") {\n        _mint(msg.sender, ' +
    supply + ' * 10 ** ' + decimals + ');\n    }\n}\n';
}

export function TokenGeneratorHub(){
 const [name,setName]=useState("FinAI Token");
 const [symbol,setSymbol]=useState("FINAI");
 const [supply,setSupply]=useState("1000000");
 const [decimals,setDecimals]=useState("18");
 const [burnable,setBurnable]=useState(true);
 const [copied,setCopied]=useState(false);
 const code=useMemo(()=>solidity(
   name.replace(/[^A-Za-z0-9]/g,"")||"FinAIToken",
   symbol.toUpperCase().replace(/[^A-Z0-9]/g,"")||"FINAI",
   Math.max(0,Math.min(18,Number(decimals)||18)),
   supply.replace(/[^0-9.]/g,"")||"1000000",
   burnable
 ),[name,symbol,supply,decimals,burnable]);
 const copy=async()=>{await navigator.clipboard.writeText(code);setCopied(true);setTimeout(()=>setCopied(false),1200)};
 const download=()=>{const url=URL.createObjectURL(new Blob([code],{type:"text/plain"}));const a=document.createElement("a");a.href=url;a.download=(symbol||"token").toLowerCase()+"-token.sol";a.click();URL.revokeObjectURL(url)};
 return <section className="module-page">
   <div className="module-hero"><div><div className="module-kicker"><Code2 size={14}/> Token laboratory</div><h1>Generate an EVM token contract without sending a transaction.</h1><p>Create an ERC-20 source template, inspect the Solidity, and export it. Deployment, private keys and real-money transactions stay outside the demo.</p></div><div className="module-orb"><ShieldCheck size={23}/></div></div>
   <div className="token-layout">
    <section className="workspace-panel">
      <div className="module-panel-head"><div><div className="module-kicker">Token design</div><h2>Contract parameters</h2></div></div>
      <label>Token name<input value={name} onChange={e=>setName(e.target.value)}/></label>
      <label>Symbol<input value={symbol} onChange={e=>setSymbol(e.target.value)}/></label>
      <label>Total supply<input value={supply} onChange={e=>setSupply(e.target.value)}/></label>
      <label>Decimals<input type="number" min="0" max="18" value={decimals} onChange={e=>setDecimals(e.target.value)}/></label>
      <label className="checkbox-line"><input type="checkbox" checked={burnable} onChange={e=>setBurnable(e.target.checked)}/> Burnable extension</label>
      <div className="data-note">Generated source is for study/prototyping. Audit the contract and review legal/compliance requirements before any public issuance.</div>
    </section>
    <section className="workspace-panel">
      <div className="module-panel-head"><div><div className="module-kicker">Generated source</div><h2>{symbol || "TOKEN"}.sol</h2></div><div className="resource-actions"><button type="button" className="secondary-module-button" onClick={copy}><Copy size={12}/>{copied?"Copied":"Copy"}</button><button type="button" className="secondary-module-button" onClick={download}><Download size={12}/>Export</button></div></div>
      <pre className="code-window">{code}</pre>
      <div className="data-note">Dependency: OpenZeppelin Contracts. No exchange listing, wallet, private-key handling or automatic deployment is included.</div>
    </section>
   </div>
 </section>
}
export default TokenGeneratorHub;
