// Diamond Holder for NV Center Sensor
// Designed for 3x3x0.5mm diamond
// Print in PLA or PETG

// Parameters
diamond_x = 3.2;  // Slightly larger for tolerance
diamond_y = 3.2;
diamond_z = 0.7;
holder_wall = 2;
holder_base = 3;

// Total dimensions
holder_x = diamond_x + 2*holder_wall;
holder_y = diamond_y + 2*holder_wall;
holder_z = diamond_z + holder_base;

// Lens mount parameters
lens_diameter = 25;  // Standard Thorlabs lens tube
lens_height = 10;

module diamond_holder() {
    difference() {
        // Main body
        cube([holder_x, holder_y, holder_z], center=true);
        
        // Diamond cavity
        translate([0, 0, holder_base/2])
            cube([diamond_x, diamond_y, diamond_z + 0.2], center=true);
        
        // Light path (bottom - laser input)
        translate([0, 0, -holder_z/2 - 0.1])
            cylinder(d=2, h=holder_base + 1, $fn=32);
        
        // Light path (top - fluorescence output)
        translate([0, 0, holder_z/2 - holder_base])
            cylinder(d=4, h=holder_base + 1, $fn=32);
        
        // Mounting holes
        translate([holder_x/2 - 1, holder_y/2 - 1, -holder_z/2])
            cylinder(d=1.5, h=2, $fn=16);
        translate([-holder_x/2 + 1, holder_y/2 - 1, -holder_z/2])
            cylinder(d=1.5, h=2, $fn=16);
        translate([holder_x/2 - 1, -holder_y/2 + 1, -holder_z/2])
            cylinder(d=1.5, h=2, $fn=16);
        translate([-holder_x/2 + 1, -holder_y/2 + 1, -holder_z/2])
            cylinder(d=1.5, h=2, $fn=16);
    }
}

module lens_mount() {
    difference() {
        // Outer cylinder
        cylinder(d=lens_diameter + 4, h=lens_height, $fn=64);
        
        // Inner hole for lens tube
        translate([0, 0, -0.1])
            cylinder(d=lens_diameter + 0.5, h=lens_height + 0.2, $fn=64);
        
        // Thread (simplified - use tap or thread insert)
        for(i=[0:3]) {
            rotate([0, 0, i*90])
                translate([lens_diameter/2 + 1.5, 0, lens_height/2])
                    rotate([0, 90, 0])
                        cylinder(d=2.5, h=2, $fn=16);
        }
    }
}

module mw_coil_holder() {
    // Holder for microwave coil around diamond
    coil_d = 12;
    coil_h = 8;
    wire_d = 0.5;
    
    difference() {
        cylinder(d=coil_d + 4, h=coil_h, $fn=32);
        translate([0, 0, -0.1])
            cylinder(d=coil_d, h=coil_h + 0.2, $fn=32);
        
        // Wire channels
        for(i=[0:4]) {
            rotate([0, 0, i*72])
                translate([coil_d/2 + 1, 0, 0])
                    cylinder(d=wire_d + 0.2, h=coil_h + 0.2, $fn=16);
        }
    }
}

// Assembly
module full_assembly() {
    translate([0, 0, holder_z/2])
        diamond_holder();
    
    translate([0, 0, holder_z + lens_height/2])
        lens_mount();
    
    translate([0, 0, -coil_h/2 - 2])
        mw_coil_holder();
}

// Export individual parts for printing
// Print this:
diamond_holder();

// Print this:
// lens_mount();

// Print this:
// mw_coil_holder();

// View full assembly:
// full_assembly();
