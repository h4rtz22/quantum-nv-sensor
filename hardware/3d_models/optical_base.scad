// Optical Base Plate for NV Sensor
// Mounts laser, optics, and detector
// Compatible with 30mm cage system or standalone

// Base plate dimensions
base_x = 150;
base_y = 100;
base_z = 8;

// Mounting hole spacing (standard 30mm cage)
hole_spacing = 30;
hole_d = 3.2;  // M3 screw

// Laser mount position
laser_x = 20;
laser_y = 50;
laser_d = 12;  // Laser module diameter

// Dichroic mount position
dichroic_x = 60;
dichroic_y = 50;
dichroic_angle = 45;

// Diamond holder position
diamond_x = 90;
diamond_y = 50;

// Detector position
detector_x = 90;
detector_y = 80;

module base_plate() {
    difference() {
        // Main plate
        cube([base_x, base_y, base_z], center=false);
        
        // Cage system mounting holes (3x3 grid)
        for(i=[0:4]) {
            for(j=[0:2]) {
                x = 30 + i*hole_spacing;
                y = 20 + j*hole_spacing;
                translate([x, y, -0.1])
                    cylinder(d=hole_d, h=base_z + 0.2, $fn=16);
            }
        }
        
        // Laser mounting hole
        translate([laser_x, laser_y, -0.1])
            cylinder(d=laser_d, h=base_z + 0.2, $fn=32);
        
        // Laser set screw holes
        translate([laser_x, laser_y - laser_d/2 - 2, base_z/2])
            rotate([0, 90, 0])
                cylinder(d=2.5, h=10, $fn=16);
        translate([laser_x, laser_y + laser_d/2 + 2, base_z/2])
            rotate([0, 90, 0])
                cylinder(d=2.5, h=10, $fn=16);
        
        // Dichroic mount slot (45 degrees)
        translate([dichroic_x, dichroic_y, base_z/2])
            rotate([0, 0, dichroic_angle])
                cube([20, 2, base_z + 0.2], center=true);
        
        // Diamond holder mounting holes
        translate([diamond_x, diamond_y, -0.1])
            cylinder(d=2, h=base_z + 0.2, $fn=16);
        translate([diamond_x + 7, diamond_y, -0.1])
            cylinder(d=2, h=base_z + 0.2, $fn=16);
        translate([diamond_x, diamond_y + 7, -0.1])
            cylinder(d=2, h=base_z + 0.2, $fn=16);
        translate([diamond_x + 7, diamond_y + 7, -0.1])
            cylinder(d=2, h=base_z + 0.2, $fn=16);
        
        // Detector mounting holes
        translate([detector_x, detector_y, -0.1])
            cylinder(d=2.5, h=base_z + 0.2, $fn=16);
        translate([detector_x + 20, detector_y, -0.1])
            cylinder(d=2.5, h=base_z + 0.2, $fn=16);
        
        // Cable management slots
        translate([10, 10, base_z/2])
            cube([80, 5, base_z + 0.2], center=true);
        translate([10, base_y - 10, base_z/2])
            cube([80, 5, base_z + 0.2], center=true);
    }
}

module laser_mount() {
    // Adjustable laser mount
    mount_h = 20;
    
    difference() {
        union() {
            // Base
            cube([25, 25, 8], center=true);
            // Tower
            translate([0, 0, mount_h/2])
                cube([20, 20, mount_h], center=true);
        }
        
        // Laser hole
        translate([0, 0, mount_h/2])
            rotate([90, 0, 0])
                cylinder(d=12.5, h=25, $fn=32);
        
        // Adjustment screw
        translate([0, 0, mount_h - 5])
            rotate([90, 0, 0])
                cylinder(d=3, h=25, $fn=16);
        
        // Mounting holes
        translate([-8, -8, -4.1])
            cylinder(d=3.2, h=8.2, $fn=16);
        translate([8, -8, -4.1])
            cylinder(d=3.2, h=8.2, $fn=16);
        translate([-8, 8, -4.1])
            cylinder(d=3.2, h=8.2, $fn=16);
        translate([8, 8, -4.1])
            cylinder(d=3.2, h=8.2, $fn=16);
    }
}

module dichroic_mount() {
    // 45 degree dichroic mirror mount
    mirror_size = 25.4;  // 1 inch
    
    difference() {
        union() {
            // Base
            cube([30, 30, 8], center=true);
            // Mirror holder at 45 degrees
            rotate([0, 0, 45])
                translate([0, 0, 15])
                    cube([mirror_size + 4, mirror_size + 4, 4], center=true);
        }
        
        // Mirror slot
        rotate([0, 0, 45])
            translate([0, 0, 15])
                cube([mirror_size + 0.5, mirror_size + 0.5, 5], center=true);
        
        // Light path hole
        rotate([0, 0, 45])
            translate([0, 0, 15])
                cylinder(d=20, h=10, $fn=32);
        
        // Mounting holes
        for(i=[0:3]) {
            rotate([0, 0, i*90])
                translate([10, 10, -4.1])
                    cylinder(d=3.2, h=8.2, $fn=16);
        }
    }
}

// Export for printing
base_plate();
// laser_mount();
// dichroic_mount();
