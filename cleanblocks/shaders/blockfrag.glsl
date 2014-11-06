#version 330 core

float PI = 3.14159265359;
uniform sampler2D TextureAtlas;
out vec4 color;


in vec3 center;  // again, should be integral.

in vec3 texposition;
in float texid;

float xytoside(vec2 xypos){
    vec2 norm = normalize(xypos);
    float angle = atan(norm.y, norm.x);
    return mod(angle*3/PI, 1.0);
}

vec4 atlaslookup(vec3 pos, float top){
   float offset = (texid-1)*.25;
   if( (top-texposition.z) < 0.0001 ){
     return texture(TextureAtlas, vec2(pos.x/4, pos.y/4) + vec2(offset, .75));
   }
   else {
     return texture(TextureAtlas, (vec2(xytoside(pos.xy), mod(pos.z, 1))/4 + vec2(offset, 0.5)));
   }
}

//TODO: side-based textures. Choose texture by texture id.
void main(){

    vec3 a = vec3((texposition.xy-center.xy)/2, texposition.z-center.z) + vec3(0.5, 0.5, 0.0);

   color = atlaslookup(a, center.z);

}