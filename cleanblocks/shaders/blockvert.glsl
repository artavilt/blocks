#version 330 core
layout(location = 0) in vec4 VertexPosition;
layout(location = 1) in float TexIDs;

out float texs;

void main(){
    texs = TexIDs;
    gl_Position = VertexPosition; //its just a pass-through to the geometry shader
}