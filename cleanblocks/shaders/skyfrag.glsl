#version 330 core

out vec3 color;


in vec2 fragdirection;


/* The vector from the current vertex position to the sun. We assume the sun is
        on the plane at infinity, so the direction vector is non-zero
        and fixed across the whole
        sphere.*/
uniform vec2 sunangle;


uniform vec3 sunwavelength; //color of the sun
uniform vec3 sunray;

uniform float g; //symmetry constant for the phase function. Between 0 and 1
uniform float g2; //


in float raylen;
in vec3 pixray;
in vec2 pixangle;

float PI = 3.14159265359;

float phase(float cosang, float intense){ //this function does a good job of finding the sun
    // but it doesn't create a good phasey kind of shape.
    return 3*(1-g2)*(1+cosang*cosang)/(2*(2+g2)*pow((1+g2-2*g*cosang), intense));
}

float nphase(vec2 angles, vec2 realangle){
    float sunang =  cos(angles.x)*cos(angles.y);
    //float phasex = phase(sunang, 1.5);
    return phase(sunang, 1.5);
}

vec3 scatcolor(float phasec){
    // wavelength of red = 6.5 (fuck units.) Then the amount it gets scattered is .00056
    // green - .001
    // blue - .002
    // so phasedwavelength = (sun.r*.25+ sun.g*.5 + sun.b*1 is an okay estimation)
    // maybe I should determine the color of the sun rays and the sky rays based on sun position.

    // in the direct sunlight areas the distance the sunlight has to travel will make scattered stuff go away
    //estimate of how far the suns rays are travelling
    float directamount = (1- 2*sunangle.y/PI);
    if( sunangle.y < .9){
        vec3 scatwave = sunwavelength * vec3(0.3, 0.5, 1) * pow(directamount, .7);
        vec3 directwave = sunwavelength/vec3(pow(0.25, directamount), pow(0.5, directamount), 1);
        // as phasec drops we want phasewave to dominate
        vec3 phasequantity =  (1-phasec)*scatwave;
        vec3 direct = phasec*directwave;
        return direct + phasequantity;
    } else{
        return vec3(0.0, 0.0, 0.0);
    }

}




void main(){
    // turn the sunray into a translation vector. translate the angles by that vector and they
    // give you the angular distance of the point from angle (0,0), where the sun now is.
    vec2 diffangles = pixangle - sunangle;
    //float scat = pow(phase(cos(diffangles.x)*cos(diffangles.y)), 1);
    color = ceil((scatcolor(nphase(diffangles, pixangle))*sunwavelength)*20)/20;
}