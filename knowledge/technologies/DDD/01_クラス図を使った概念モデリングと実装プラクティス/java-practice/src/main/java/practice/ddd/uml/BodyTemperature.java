package practice.ddd.uml;

record BodyTemperature(double celsius) {
  static BodyTemperature celsius(double value) {
    return new BodyTemperature(value);
  }

  @Override
  public String toString() {
    return celsius + "C";
  }
}

