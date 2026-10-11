const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.join(__dirname, 'assets/icons/lucide');
const icons = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(root, 'IconMap.js'), 'utf8'), icons);
const codes = JSON.parse(fs.readFileSync(path.join(root, 'codepoints.json'), 'utf8'));
assert(process.argv[2], 'Run update-controls.py --bar to supply the actual font charset');
const charset = process.argv[2]
  .trim().split(/\s+/).map(range => range.split('-').map(code => parseInt(code, 16)));
assert(charset.every(([first]) => first >= 0xe000), 'Empty ASCII glyphs would hide RPM and percentage text');
for (const [legacy, name] of Object.entries(icons.names)) {
  assert(Number.isInteger(codes[name]), `Missing Lucide icon: ${name}`);
  assert(charset.some(([first, last = first]) => codes[name] >= first && codes[name] <= last), `Missing font glyph: ${name}`);
  assert.equal(icons.render(legacy), String.fromCodePoint(codes[name]));
}
assert.equal(icons.render('1900 RPM'), '1900 RPM');
assert.equal(icons.render('EN العربية 12:09'), 'EN العربية 12:09');
assert.equal(icons.render('󰈐 1900 RPM'), String.fromCodePoint(codes.fan) + ' 1900 RPM');
assert.equal(icons.render('50% '), '50% ' + String.fromCodePoint(codes.power));
assert.equal(icons.render('unknown 🐧'), 'unknown 🐧');
assert.notEqual(icons.render('󰤨'), icons.render('󰤟'));
assert.notEqual(icons.render(''), icons.render(''));
assert.notEqual(icons.render('󰂱'), icons.render('󰂲'));
const power = vm.createContext({});
vm.runInContext(fs.readFileSync('/usr/share/omarchy/shell/plugins/panels/power/Model.js', 'utf8'), power);
const states = {Charging: 1, Discharging: 2, FullyCharged: 4, PendingCharge: 5};
for (let level = 0; level <= 10; level++) {
  for (const state of Object.values(states)) {
    for (const onBattery of [true, false]) {
      const legacy = power.batteryIcon({isPresent: true, percentage: level / 10, state}, onBattery, states);
      assert(icons.names[legacy]?.startsWith('battery'), `Unmapped battery state: ${level}, ${state}, ${onBattery}`);
    }
  }
}
assert.notEqual(icons.render('󰁺'), icons.render('󰁹'));
assert.notEqual(icons.render('󰂅'), icons.render('󰁹'));
assert(fs.statSync(path.join(root, 'lucide.ttf')).size > 10000);
assert(fs.readFileSync(path.join(root, 'LICENSE'), 'utf8').includes('Permission'));
console.log('PASS: Lucide names, all battery states, mixed text, Unicode and license');
