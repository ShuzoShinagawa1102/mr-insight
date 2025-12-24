package practice.ddd.uml;

public final class Main {
  public static void main(String[] args) {
    System.out.println("=== 抽象化 / 一般化 ===");
    Demos.abstractionAndGeneralization();

    System.out.println();
    System.out.println("=== 構造化（関連 / 集約・コンポジション / 依存）===");
    Demos.structuringRelationships();

    System.out.println();
    System.out.println("=== 実現（interface）===");
    Demos.realization();

    System.out.println();
    System.out.println("=== 同一性 / 等価性（Entity / Value Object）===");
    Demos.identityAndEquivalence();
  }
}

