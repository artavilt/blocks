
#version 330 core
/* input:
        points on a square grid, and data about them...
    output:
        hexagonal columns up to the z-value. passes texture data to the frag shader.
*/


layout(points) in;
layout(triangle_strip, max_vertices=20) out;

in float texs[1];

out vec3 center;  // center of the tile we are currently shading pre-projection
                  // the frag shader receives it to map into UV coords.
smooth out vec3 texposition;
out float texid;

uniform mat4 Transform;
uniform vec3 campos;

float PI = 3.14159265359;

vec2 hexpoint( uint ptnum, vec2 pos ){
    return vec2( cos( ptnum * PI/3 ) + 1.5*pos.x,
                sin( ptnum * PI/3 ) + (2*pos.y +mod(pos.x, 2))*sin(2*PI/3));
}


vec4 hexvert( uint ptnum, vec2 pos, float z ){
    return vec4(  hexpoint( ptnum,  pos ), z, 1.0);
}

//TODO: texture indexing
void main()
{
    /* center of the top of the column */
    vec4 cent = gl_in[0].gl_Position;
    center = vec3((cent.x)*1.5,
                  (2*(cent.y) +mod(cent.x, 2))*sin(2*PI/3), (cent.z));
    vec4 pos;

    // calculate the amount we should rotate the culled prisms to stick them in front
    // of your eye
    int ang;
    //flat ray from cam to hex
    vec2 ray = normalize(center.xy + campos.xy); //why addition I am missing something here
    float zangle = atan(ray.x, ray.y);
    //the index that is closest to the center of the view. We rotate the culled prism to face the camera.
    // this kills 6 triangles per vertice. TODO: render from the top/bottom depending on xangle.
    ang = -int(floor((3*zangle)/PI+.5)); //trial and error says -2 is the right offset


    const int poslist[28]  =  int[28](// 3 sides of the hexagonal prism (I think there is a mistake here,
                                      // should be 4 but only 3 get rendered. Bad!)
                                        0,0,
                                        0,1,
                                        5,0,
                                        5,1,
                                        4,0,
                                        4,1,
                                        3,0,
                                        3,1,
                                        //the top of the hexagonal prism
                                        5,1,
                                        0,1,
                                        4,1,
                                        1,1,
                                        3,1,
                                        2,1);
    // the poslist should be rotated based on the pos of the viewer, so that 0 faces the viewer
    // so the z-angle of the viewer should be passed in as a uniform. Then we can just trial and error the
    // right angle.

    //the sides of the prisms
    for (int i = 0; i < 14; i+=2){
        vec4 thisvert = hexvert(int(mod(poslist[i] + ang, 6)), cent.xy,  cent.z*poslist[i+1]);
        texposition = thisvert.xyz;
        vec4 pos = Transform * thisvert;
        if (pos.w > 0.05){
            gl_Position = vec4(pos.xyz/pos.w, 1.0);
            texid = texs[0];
            EmitVertex();
        }
    }
    // the top (or bottom) of the prisms
    for (int i = 14; i < 28; i+=2){
        vec4 thisvert = hexvert(int(mod(poslist[i] + ang, 6)), cent.xy,  cent.z*poslist[i+1]);
        texposition = thisvert.xyz;
        vec4 pos = Transform * thisvert;
        if (pos.w > 0.05){
            gl_Position = vec4(pos.xyz/pos.w, 1.0);
            texid = texs[0];
            EmitVertex();
        }
    }

    EndPrimitive();

}
