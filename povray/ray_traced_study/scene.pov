// Title:        MakeRoom demo scene
// Written by:   Matthew Goulet <povray@bherring.cotse.net>
// Created on:   July 3, 2008
// Last updated: July 11, 2008
//
// This file is licensed under the terms of the CC-LGPL
//
// +W800 +H600 +AM2 +A0.03
//
#version 3.61;


#include "colors.inc"
#include "makeroom.inc"
#include "metals.inc"




#declare Use_Area = yes;
#declare Use_Glass = yes;
#declare Use_Textures = yes;
#declare Use_Blur = no;
#declare Use_HQ_Blur = no;

#declare Use_Moon = yes;
#declare Use_Daylight = no;
#declare Lamp_On = yes;
#declare Night_Light_On = yes;
 

global_settings {
  assumed_gamma 1.0
  max_trace_level 15
}

#include "chair_POV_geom.inc"
#include "telescope_POV_geom.inc"
#include "couch_geom.inc"


camera {
  location <5, 0, -80>
  up y 
  right x * image_width/image_height
  look_at 0
  #if(Use_Blur)
    aperture 0.008
    focal_point 0
    #if(Use_HQ_Blur)
      blur_samples 512
      confidence 0.96
      variance 1/100000
    #else
      blur_samples 100
      confidence 0.9
      variance 1/10000
    #end
  #end
}

light_source {
              <10, 10, -49>
              color rgb <.15,.15,.15>
}


#declare Incandescent = rgb <255, 178, 91>/255;
#declare Candle_Flame = rgb <255, 130, 0>/255;
#declare Moonlight = rgb <255, 215, 166>/255;



light_source {
  z * 600, Moonlight * (3)
  #if(Use_Area)
    area_light
    x * 10, y * 10, 33, 33
    circular
    adaptive 2
    jitter
  #end
  fade_power 2
  fade_distance 500
  parallel
  point_at 0
  rotate <-45, 12, 0>
}


#declare Ceiling_T = 
  texture {
    pigment { 
      bozo
      color_map {
        [0 rgb <1.0000, 0.9290, 0.7370> ]
        [1 MR_AntiqueWhite]
      }
    }
  }
  
#declare Floor_T = 
  texture{
    pigment {
      image_map{jpeg "./images/floor.jpg" /*gamma srgb*/  transmit all 0 }
    }
  }

#declare MR_Ceiling_T = Ceiling_T;
#declare MR_Floor_T = Floor_T;

#declare MR_Doors      = array[1] { 1 };
#declare MR_Doors_Side = array[1] { -x };
#declare MR_Doors_Size = array[1] { <40, 70> };
#declare MR_Doors_Pos  = array[1] { z * 40 };

#declare MR_Windows      = array[5] { 4, 4, 4, 4, 4 };
#declare MR_Windows_Side = array[5] { z, z, x, x, x };
#declare MR_Windows_Size = array[5] { <30, 40>, <30, 40>, <30, 40>, <30, 40>, <30, 40> };
#declare MR_Windows_Pos  = array[5] { x * 20, x * -20, z * 50, z * 0, z * -50 };
#declare MR_Windows_Thickness = 1;
#declare MR_Windows_Use_Glass = Use_Glass;

#declare MR_Baseboard = yes;

#declare MR_Crown = yes;

#declare Room_1 = MakeRoom(<100, 80, 150>);
  

#declare Lamp = 
  union {
    cone { 
      0, 5, y * 10, 3
      open
      double_illuminate
      pigment { White }
      finish {
        ambient 0
        diffuse 1
      }
    }
    #if(Lamp_On)
      light_source {
        y * 6, Incandescent * 4
        #if(Use_Area)
          area_light
          x * 2, y * 2, 33, 33
          adaptive 2
          circular
          orient
        #end
        fade_power 2
        fade_distance 7
      }
    #end
    union {
      cylinder { y * -4, y * 3, 0.5 }
      intersection {
        box { -0.75, 0.75 }
        sphere { 0, 1 }
        bounded_by {
          box { -0.75, 0.75 }
        }
        translate y * -5
      }
      cylinder { y * -5, <0, -5, 7>, 0.5 }
      cone { <0, -5, 7>, 0.5, <0, -5, 8>, 2 }
      texture {
        pigment { P_Brass3 }
        finish {
          ambient 0
          diffuse 0.05
          #if(Use_Textures)
            specular 1.9
            roughness 0.005272
            brilliance 3
            metallic
            reflection {
              0.475, 0.95
              metallic
            }
            conserve_energy
          #end
        }
      }
    }
    translate <0, 5, -8>
  }

#declare rug =
  
  union{
  sphere{ <0,-5,-65>, 1

          translate<0,5,65>
          scale<1,.05,1.3>
          translate<0,-5,-65>
             
    }


    box{ <0,-6,-64> <3,-4,-66>

          translate<-1.5,5,65>
          scale<1,.03,1.3>
          translate<1.5,-5,-65>
            
    }

   
    sphere{ <3,-5,-65>, 1
   
          translate<0,5,65>
          scale<1,.05,1.3>
          translate<0,-5,-65>
                
    }
  
    texture{   pigment {
    agate
    agate_turb 0.5
    
  }
 }

  }
  
#declare Night_Light =
  union {
    intersection {
      sphere {
        0, 5
        scale <0.5, 1, 0.5>
      }
      box { <-2.5, 0, -2.5>, <2.5, 5, 0> }
      bounded_by {
        box { <-2.5, 0, -2.5>, <2.5, 5, 0> }
      }
      double_illuminate
      texture {
        pigment { White }
        finish {
          ambient 0
          diffuse 1
          #if(Use_Textures)
            specular 0.5
            roughness 0.05
            reflection {
              0, 0.2
              fresnel
            }
            conserve_energy
          #end
        }
      }
    }
    #if(Night_Light_On)
      light_source {
        <0, 2, -1>, Incandescent * 5
        fade_power 2
        fade_distance 2
      }
    #end
    box { <-1, -2.5, -2>, x }
    cylinder { y * -1.25, <0, -1.25, 0.5>, 1 }
    texture {
      pigment { rgb <0.9610, 0.9060, 0.6350> }
      #if(Use_Textures)
        finish {
          specular 0.75
          roughness 0.04
          reflection {
            0, 0.3
            fresnel
          }
          conserve_energy
        }
      #end
    }
    interior {
      ior 1.51
    }
    translate <0, 1.25, -0.5>
  }
  
sphere {
  0, 11000
  inverse
  texture {
    pigment { Black }
    finish {
      ambient 0
      diffuse 0
    }
  }
}

object { Room_1 }  

object {
  Lamp
  rotate y * -90
  translate x * -50
}
  
object {
  Night_Light
  rotate y * -90
  translate <-50, -32, 10>
}

object{
      chair_
      scale <1.7,1.7,1.7>
      rotate <0,90,0> 
      translate <6.4, -3, -71>
}

object{
      telescope_
      scale <0.03,0.033,0.03>
      rotate <0,90,0> 
      translate <9, -5, -65>
      }

object{
      rug
      translate <6.55, 0, .5>
      }

object{
      ThomasvilleSofa_FINAL01_
      scale <1.75,1.75,1.75>
      rotate <13,100,14> 
      translate<.3,-5.1,-63>
      
      }