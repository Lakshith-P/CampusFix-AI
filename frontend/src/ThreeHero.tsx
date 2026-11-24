import {useEffect,useRef} from 'react';
import * as THREE from 'three';

export default function ThreeHero(){
  const host=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    const el=host.current;if(!el)return;
    const scene=new THREE.Scene();
    const camera=new THREE.PerspectiveCamera(38,el.clientWidth/el.clientHeight,.1,100);
    camera.position.set(0,0,7);
    const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
    renderer.setSize(el.clientWidth,el.clientHeight);
    renderer.setClearColor(0x000000,0);
    el.appendChild(renderer.domElement);
    const group=new THREE.Group();scene.add(group);
    const geometry=new THREE.IcosahedronGeometry(1.45,5);
    const material=new THREE.MeshPhysicalMaterial({color:0x789681,roughness:.22,metalness:.12,clearcoat:1,clearcoatRoughness:.12});
    const orb=new THREE.Mesh(geometry,material);group.add(orb);
    const wire=new THREE.Mesh(new THREE.IcosahedronGeometry(1.53,2),new THREE.MeshBasicMaterial({color:0xe4eee2,wireframe:true,transparent:true,opacity:.16}));
    group.add(wire);
    const ring=new THREE.Mesh(new THREE.TorusGeometry(2.05,.012,8,160),new THREE.MeshBasicMaterial({color:0xd77c61,transparent:true,opacity:.8}));
    ring.rotation.x=1.15;ring.rotation.y=.35;group.add(ring);
    const particles=new THREE.Group();
    for(let i=0;i<75;i++){const dot=new THREE.Mesh(new THREE.SphereGeometry(.018,8,8),new THREE.MeshBasicMaterial({color:i%4===0?0xd77c61:0x789681}));const a=Math.random()*Math.PI*2;const r=2.3+Math.random()*1.4;dot.position.set(Math.cos(a)*r,(Math.random()-.5)*3,Math.sin(a)*r);particles.add(dot)}
    scene.add(particles);
    const light=new THREE.PointLight(0xffffff,45);light.position.set(3,4,5);scene.add(light);
    scene.add(new THREE.AmbientLight(0xffffff,1.7));
    let frame=0,raf=0;
    const animate=()=>{raf=requestAnimationFrame(animate);frame+=.006;group.rotation.y=frame*.35;group.rotation.x=Math.sin(frame*.5)*.12;ring.rotation.z=frame*.2;particles.rotation.y=-frame*.12;renderer.render(scene,camera)};
    animate();
    const resize=()=>{if(!host.current)return;camera.aspect=host.current.clientWidth/host.current.clientHeight;camera.updateProjectionMatrix();renderer.setSize(host.current.clientWidth,host.current.clientHeight)};
    window.addEventListener('resize',resize);
    return()=>{cancelAnimationFrame(raf);window.removeEventListener('resize',resize);geometry.dispose();material.dispose();wire.geometry.dispose();(wire.material as THREE.Material).dispose();ring.geometry.dispose();(ring.material as THREE.Material).dispose();renderer.dispose();el.removeChild(renderer.domElement)};
  },[]);
  return <div className="three-hero" ref={host} aria-label="Animated three dimensional CampusFix AI orb"/>;
}
