// Shared OpenSCAD helpers for lettersign generated files.
// Canonical copy lives in the lettersign package; build syncs to projects/lettersign_common.scad.

module lettersign_post(position, radius, height) {
  translate([position[0], position[1], 0])
    cylinder(r=radius, h=height);
}
