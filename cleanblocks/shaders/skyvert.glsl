#version 330 core

layout(location = 0) in vec4 VertexPosition;

//out vec2 texposition;

uniform mat4 look;
uniform float aspect;

float PI = 3.14159265359;



// vector in the direction the camera is looking. This is the center of the thing, so we find the point on the sphere
// by adding the xyz of the vertex position? No. vertexposition.x = cos(theta) where theta = X-angular offset from
// center, which is lookdirection.
// vertexposition.y = cos(gamma) where gamma = Z-angular offset from center, which is lookdirection.
// so we should really take the look direction as a vec2 in polar coordinates.
uniform vec2 lookangles;

uniform vec2 FOV;

uniform float prad; //radius of the planet relative to atmosphere. (0 = no atmosphere)



uniform float scaledepth;

uniform vec3 sunray;

uniform float intensity;
//uniform vec3 invwavelength;


int nsamples = <NUM_SAMPLES>;

out vec2 pixangle;
out vec3 pixray;
out vec3 raycolor;
out vec3 miecolor;
out float raylen;

vec3 raytoplanetray(vec3 look, vec3 ray){
    //this is good but it should actually rotate the position of the vertex.
    // right now x and y are basically
    // this is a super-simplified sphere intersection equation.
    vec3 point = prad*look;
    vec3 rt = ray - point;
    float dl = dot(rt, point);
    float mag = dot(rt, rt);
    float pmag = dot(point, point);
    float answer =  (-dl + sqrt(dl*dl - mag*(pmag-1)))/mag;
    rt *= answer;
    return rt;
}



void main(){
    vec2 angles = vec2(VertexPosition.x*FOV.x/2,
                       -VertexPosition.y*FOV.y/2);

    pixangle = lookangles + angles;


    pixray = vec3(sin(pixangle.x)*cos(pixangle.y),  cos(pixangle.x)*cos(pixangle.y), -sin(pixangle.y));
    vec3 ray = raytoplanetray(vec3(1.0,0.0,0.0), pixray);
    raylen = length(ray);


    mat4 persp = mat4(vec4(1, 0, 0, 0),
                      vec4(0, 1, 0, 0),
                      vec4(0, 0, 1, 0),
                      vec4(0, 0, 0, 1));
    //fragdirection = pixangle;
    gl_Position = VertexPosition;

}