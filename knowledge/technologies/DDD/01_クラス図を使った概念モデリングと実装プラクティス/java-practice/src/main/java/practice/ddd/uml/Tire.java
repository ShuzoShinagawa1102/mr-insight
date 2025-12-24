package practice.ddd.uml;

final class Tire {
  private final TireSerialNumber serialNumber;
  private final TireSpec spec;
  private boolean burned;

  Tire(TireSerialNumber serialNumber, TireSpec spec) {
    this.serialNumber = serialNumber;
    this.spec = spec;
  }

  void burn() {
    burned = true;
  }

  String describe() {
    return "{serial=" + serialNumber.value() + ", spec=" + spec + ", burned=" + burned + "}";
  }
}

