/* Legacy Beta path compatibility · official ecosystem toolbar owns visible utilities. */
(()=>{"use strict";try{
 document.getElementById("vnvBetaProgramLink")?.remove();
 document.getElementById("vnvBetaProgramFallback")?.remove();
 if(window.VNVBetaProgram){window.VNVEcosystemToolbar?.mount?.();return;}
 if(document.querySelector('script[data-vnv-global-beta-compat]'))return;
 const s=document.createElement("script");s.src="https://vervenveda.com/assets/vnv-beta-link.js";s.defer=true;s.dataset.vnvGlobalBetaCompat="1";
 (document.head||document.documentElement).append(s);
}catch{}})();
