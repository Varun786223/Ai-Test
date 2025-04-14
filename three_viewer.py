import streamlit.components.v1 as components
import os

def create_3d_viewer(model_path: str) -> None:
    """
    Creates a Three.js viewer component for displaying 3D models.
    
    Args:
        model_path (str): Path to the 3D model file (GLTF/GLB)
    """
    # Convert path to use forward slashes for web compatibility
    model_path = model_path.replace('\\', '/')
    
    # HTML template for Three.js viewer
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>3D Model Viewer</title>
        <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/build/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/loaders/GLTFLoader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/controls/OrbitControls.js"></script>
        <style>
            body {{ margin: 0; }}
            canvas {{ display: block; }}
        </style>
    </head>
    <body>
        <script>
            // Scene setup
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
            directionalLight.position.set(0, 1, 0);
            scene.add(directionalLight);
            
            // Controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Load model
            const loader = new THREE.GLTFLoader();
            loader.load(
                '{model_path}',
                function (gltf) {{
                    const model = gltf.scene;
                    scene.add(model);
                    
                    // Center and scale model
                    const box = new THREE.Box3().setFromObject(model);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    
                    model.position.sub(center);
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const scale = 5 / maxDim;
                    model.scale.multiplyScalar(scale);
                    
                    // Position camera
                    camera.position.set(0, 0, 5);
                    controls.target.set(0, 0, 0);
                }},
                undefined,
                function (error) {{
                    console.error('An error occurred loading the model:', error);
                }}
            );
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
            
            // Handle window resize
            window.addEventListener('resize', function() {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }});
        </script>
    </body>
    </html>
    """
    
    # Display the viewer
    components.html(html, height=600) 