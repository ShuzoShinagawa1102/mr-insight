import DownloadIcon from "@mui/icons-material/Download";
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
  useMediaQuery,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useEffect, useMemo, useRef, useState } from "react";
import { getIndexedDocs, hasIndexYear, type IndexedDoc } from "../data/yuhouIndex";
import type { Company } from "../types";

export type YearDownloadOptions = {
  year: number;
  includeCorrections: boolean;
  fileType: 1 | 2;
  docs?: IndexedDoc[];
};

type YearStatus =
  | { kind: "unchecked" }
  | { kind: "checking" }
  | { kind: "available"; docs: IndexedDoc[] }
  | { kind: "none" }
  | { kind: "missing" };

export default function YearDownloadsDialog(props: {
  open: boolean;
  company: Company | null;
  apiKey: string;
  onClose: () => void;
  onConfirm: (options: YearDownloadOptions) => void;
}) {
  const company = props.company;
  const apiKey = props.apiKey;
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const currentYear = new Date().getFullYear();
  const years = useMemo(
    () => Array.from({ length: 10 }, (_, i) => currentYear - i),
    [currentYear],
  );

  const [includeCorrections, setIncludeCorrections] = useState(true);
  const [fileType, setFileType] = useState<1 | 2>(2);
  const [statusByYear, setStatusByYear] = useState<Record<number, YearStatus>>({});

  const canUse = Boolean(company && apiKey.trim());

  const runIdRef = useRef(0);

  async function ensureYearLoaded(year: number): Promise<IndexedDoc[]> {
    if (!company) return [];
    if (!hasIndexYear(year)) {
      setStatusByYear((prev) => ({ ...prev, [year]: { kind: "missing" } }));
      return [];
    }

    const existing = statusByYear[year];
    if (existing?.kind === "available") return existing.docs;
    if (existing?.kind === "none") return [];
    if (existing?.kind === "missing") return [];

    setStatusByYear((prev) => ({ ...prev, [year]: { kind: "checking" } }));
    try {
      const docs = await getIndexedDocs({ company, year, includeCorrections });
      setStatusByYear((prev) => ({
        ...prev,
        [year]: docs.length > 0 ? { kind: "available", docs } : { kind: "none" },
      }));
      return docs;
    } catch (e) {
      console.error("Failed to load index for year", year, e);
      setStatusByYear((prev) => ({ ...prev, [year]: { kind: "missing" } }));
      return [];
    }
  }

  useEffect(() => {
    if (!props.open) return;
    if (!company) return;

    runIdRef.current += 1;
    const runId = runIdRef.current;

    setStatusByYear({});

    const load = async () => {
      for (const year of years) {
        if (runIdRef.current !== runId) return;
        // eslint-disable-next-line no-await-in-loop
        await ensureYearLoaded(year);
      }
    };
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.open, company?.secCode4, includeCorrections]);

  function statusChip(status: YearStatus) {
    switch (status.kind) {
      case "unchecked":
        return { label: "未確認", color: "default" as const };
      case "checking":
        return { label: "確認中…", color: "default" as const };
      case "available":
        return { label: `あり（${status.docs.length}）`, color: "success" as const };
      case "none":
        return { label: "なし", color: "warning" as const };
      case "missing":
        return { label: "未収録", color: "default" as const };
    }
  }

  return (
    <Dialog
      open={props.open}
      onClose={props.onClose}
      fullWidth
      maxWidth="md"
      fullScreen={isMobile}
    >
      <DialogTitle>年度ごとにダウンロード</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {!company ? <Alert severity="info">会社が選択されていません。</Alert> : null}
          {company ? (
            <Typography variant="body2">
              {company.secCode4} {company.name}（{company.market}）
            </Typography>
          ) : null}

          {!apiKey.trim() ? (
            <Alert severity="error">
              EDINET APIキーが未設定です（`.env.local` の `VITE_EDINET_API_KEY`）。
            </Alert>
          ) : null}

          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
            <TextField
              select
              label="ファイル形式"
              size="small"
              value={fileType}
              onChange={(e) => setFileType(Number(e.target.value) as 1 | 2)}
              sx={{ minWidth: 220 }}
            >
              <MenuItem value={2}>PDF（type=2）</MenuItem>
              <MenuItem value={1}>ZIP（XBRL等 / type=1）</MenuItem>
            </TextField>
            <Button
              variant={includeCorrections ? "contained" : "outlined"}
              onClick={() => {
                setIncludeCorrections(true);
              }}
            >
              訂正含む
            </Button>
            <Button
              variant={!includeCorrections ? "contained" : "outlined"}
              onClick={() => {
                setIncludeCorrections(false);
              }}
            >
              訂正除外
            </Button>
          </Stack>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: isMobile
                ? "repeat(1, minmax(0, 1fr))"
                : "repeat(2, minmax(0, 1fr))",
              gap: 1,
            }}
          >
            {years.map((year) => {
              const status = statusByYear[year] ?? { kind: "unchecked" as const };
              const chip = statusChip(status);
              const isChecking = status.kind === "checking";
              const canDownload =
                canUse && status.kind === "available" && status.docs.length > 0 && !isChecking;

              return (
                <Box
                  key={year}
                  sx={{
                    border: "1px solid rgba(0,0,0,0.12)",
                    borderRadius: 1,
                    p: 1,
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                  }}
                >
                  <Typography sx={{ width: 90 }}>{year}年度</Typography>
                  <Chip size="small" label={chip.label} color={chip.color} />
                  <Box sx={{ flex: 1 }} />
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={<DownloadIcon />}
                    disabled={!canDownload}
                    onClick={async () => {
                      const docs =
                        status.kind === "available"
                          ? status.docs
                          : await ensureYearLoaded(year);
                      if (docs.length === 0) return;
                      props.onConfirm({ year, includeCorrections, fileType, docs });
                    }}
                  >
                    DL
                  </Button>
                </Box>
              );
            })}
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={props.onClose}>閉じる</Button>
      </DialogActions>
    </Dialog>
  );
}
