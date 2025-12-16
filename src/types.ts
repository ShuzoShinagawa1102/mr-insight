export type Company = {
  secCode4: string;
  secCode5: string;
  name: string;
  market: string;
};

export type EdinetDocument = {
  docID: string;
  edinetCode?: string | null;
  secCode?: string | null;
  filerName?: string | null;
  docDescription?: string | null;
  formCode?: string | null;
  ordinanceCode?: string | null;
  docTypeCode?: string | null;
  submitDateTime?: string | null;
};

