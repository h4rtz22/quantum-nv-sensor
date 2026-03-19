// Underwater Housing for NV Sensor
// IP68 rated, depth rating 50m
// Material: PETG or ABS (waterproof)

// Housing dimensions
housing_d = 80;
housing_h = 120;
wall_thickness = 4;

// Optical window
window_d = 25;
window_thickness = 5;

// Connector port
conn_d = 20;

// Mounting points
mount_w = 20;

module main_housing() {
    difference() {
        // Outer cylinder
        cylinder(d=housing_d, h=housing_h, $fn=64);
        
        // Inner cavity
        translate([0, 0, wall_thickness])
            cylinder(d=housing_d - 2*wall_thickness, h=housing_h - wall_thickness + 0.1, $fn=64);
        
        // Optical window opening (front)
        translate([0, 0, -0.1])
            cylinder(d=window_d + 1, h=wall_thickness + 0.2, $fn=32);
        
        // Connector opening (back)
        translate([0, 0, housing_h - wall_thickness - 0.1])
            cylinder(d=conn_d + 1, h=wall_thickness + 0.2, $fn=32);
        
        // O-ring groove (front)
        translate([0, 0, wall_thickness - 2])
            difference() {
                cylinder(d=housing_d - 2, h=2, $fn=64);
                cylinder(d=housing_d - 6, h=2.1, $fn=64);
            }
    }
}

module end_cap() {
    cap_h = 15;
    
    difference() {
        union() {
            // Main cap
            cylinder(d=housing_d + 4, h=cap_h, $fn=64);
            
            // Grip texture
            for(i=[0:11]) {
                rotate([0, 0, i*30])
                    translate([housing_d/2 + 2, 0, cap_h/2])
                        cylinder(d=3, h=cap_h - 2, $fn=16);
            }
        }
        
        // Inner cavity for sensor
        translate([0, 0, 4])
            cylinder(d=housing_d - 2*wall_thickness - 2, h=cap_h, $fn=64);
        
        // Optical window mount
        translate([0, 0, -0.1])
            cylinder(d=window_d + 2, h=6, $fn=32);
        
        // Window retaining ring threads (simplified)
        translate([0, 0, 4])
            cylinder(d=window_d + 6, h=2, $fn=32);
        
        // Mounting holes for window
        for(i=[0:3]) {
            rotate([0, 0, i*90])
                translate([window_d/2 + 3, 0, -0.1])
                    cylinder(d=2, h=6, $fn=16);
        }
    }
}

module optical_window() {
    // Sapphire or borosilicate glass window
    difference() {
        cylinder(d=window_d, h=window_thickness, $fn=32);
        
        // Bevel edge
        translate([0, 0, window_thickness - 1])
            cylinder(d1=window_d, d2=window_d - 2, h=1, $fn=32);
        
        // Mounting holes
        for(i=[0:3]) {
            rotate([0, 0, i*90])
                translate([window_d/2 - 3, 0, -0.1])
                    cylinder(d=2, h=window_thickness + 0.2, $fn=16);
        }
    }
}

module cable_gland() {
    // Waterproof cable entry
    gland_h = 25;
    
    difference() {
        union() {
            // Outer body
            cylinder(d=conn_d, h=gland_h, $fn=32);
            
            // Threads (simplified)
            for(i=[0:5]) {
                translate([0, 0, 10 + i*2])
                    cylinder(d=conn_d + 1, h=1, $fn=32);
            }
            
            // Nut
            translate([0, 0, gland_h - 5])
                cylinder(d=conn_d + 6, h=5, $fn=6);
        }
        
        // Cable hole
        translate([0, 0, -0.1])
            cylinder(d=8, h=gland_h + 0.2, $fn=32);
        
        // Compression area
        translate([0, 0, gland_h - 10])
            cylinder(d=12, h=8, $fn=32);
    }
}

module mounting_bracket() {
    // For attaching to diver's equipment
    bracket_w = 40;
    bracket_h = 60;
    
    difference() {
        union() {
            // Base plate
            cube([bracket_w, 10, bracket_h], center=true);
            
            // Housing clamp
            translate([0, housing_d/4 + 5, 0])
                difference() {
                    cylinder(d=housing_d + 8, h=20, $fn=64, center=true);
                    cylinder(d=housing_d + 1, h=21, $fn=64, center=true);
                    translate([0, -housing_d/2, 0])
                        cube([housing_d + 10, housing_d, 25], center=true);
                }
        }
        
        // Strap slots
        translate([-15, 0, 15])
            cube([8, 12, 25], center=true);
        translate([15, 0, 15])
            cube([8, 12, 25], center=true);
        translate([-15, 0, -15])
            cube([8, 12, 25], center=true);
        translate([15, 0, -15])
            cube([8, 12, 25], center=true);
        
        // Mounting holes
        translate([0, 0, 25])
            rotate([90, 0, 0])
                cylinder(d=4, h=15, $fn=16);
    }
}

// Export for printing
// main_housing();
// end_cap();
// optical_window();
// cable_gland();
// mounting_bracket();

// Assembly view
module full_assembly() {
    main_housing();
    
    translate([0, 0, -15])
        end_cap();
    
    translate([0, 0, -5])
        optical_window();
    
    translate([0, 0, housing_h])
        cable_gland();
    
    translate([housing_d/2 + 25, 0, housing_h/2])
        mounting_bracket();
}

full_assembly();
