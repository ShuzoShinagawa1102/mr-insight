import SearchIcon from "@mui/icons-material/Search";
import {
  Alert,
  AppBar,
  Box,
  CircularProgress,
  InputAdornment,
  Link,
  List,
  ListItemButton,
  ListItemText,
  Snackbar,
  Stack,
  TextField,
  Toolbar,
  Typography,
  useMediaQuery,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useMemo, useState } from "react";
import { downloadDocumentBlob } from "./api/edinet";
import Logo from "./components/Logo";
import YearDownloadsDialog, {
  type YearDownloadOptions,
} from "./components/YearDownloadsDialog";
import companiesData from "./data/tse_companies.json";
import { downloadBlob, sanitizeFileName } from "./lib/download";
import { buildSearchKey, tokenizeQuery } from "./lib/searchNormalize";
import type { Company, EdinetDocument } from "./types";

export default function App() {
  const companies = companiesData as Company[];
  const apiKey =
    (import.meta.env.VITE_EDINET_API_KEY as string | undefined) ?? "";
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const [searchText, setSearchText] = useState("");
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    message: string;
    severity: "success" | "error" | "info";
  } | null>(null);

  const rows = useMemo(() => {
    const base = companies.map((c, i) => ({
      id: i,
      ...c,
      _search: buildSearchKey([c.secCode4, c.name, c.market]),
    }));
    const tokens = tokenizeQuery(searchText);
    if (tokens.length === 0) return base;
    return base.filter((c) =>
      tokens.every((t) => String(c._search).includes(t)),
    );
  }, [companies, searchText]);

  const columns = useMemo<GridColDef[]>(
    () => [
      { field: "secCode4", headerName: "証券コード", width: 130, sortable: true },
      { field: "name", headerName: "銘柄名", flex: 1, minWidth: 240, sortable: true },
      { field: "market", headerName: "市場", width: 170, sortable: true },
    ],
    [],
  );

  async function handleConfirmDownload(options: YearDownloadOptions) {
    if (!selectedCompany) return;
    if (!apiKey.trim()) {
      setSnackbar({
        severity: "error",
        message:
          "EDINET APIキーが未設定です（GitHub Pages の場合は Secrets 設定を確認してください）。",
      });
      return;
    }
    setDialogOpen(false);

    try {
      setBusy(true);
      const docs: Array<
        Pick<EdinetDocument, "docID" | "submitDateTime" | "docDescription">
      > = options.docs && options.docs.length > 0 ? options.docs : [];

      if (docs.length === 0) {
        setSnackbar({
          severity: "info",
          message: "対象年度の有報が見つかりませんでした（未収録の可能性があります）。",
        });
        return;
      }

      setSnackbar({
        severity: "info",
        message: `ダウンロード中…（${docs.length}件）`,
      });
      for (const doc of docs) {
        const submitted =
          (doc.submitDateTime ?? "").split(" ")[0] || String(options.year);
        const desc = doc.docDescription ?? "有報";
        const ext = options.fileType === 2 ? "pdf" : "zip";
        const filename = sanitizeFileName(
          `${selectedCompany.secCode4}_${selectedCompany.name}_${submitted}_${desc}_${doc.docID}.${ext}`,
        );
        const blob = await downloadDocumentBlob(
          doc.docID,
          options.fileType,
          apiKey,
        );
        await downloadBlob(blob, filename);
      }

      setSnackbar({
        severity: "success",
        message: `ダウンロード完了: ${docs.length}件`,
      });
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      setSnackbar({ severity: "error", message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box>
      <AppBar position="sticky" color="transparent" elevation={0}>
        <Toolbar sx={{ gap: 2, minHeight: isMobile ? 64 : 72 }}>
          <Box
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            sx={{ cursor: "pointer", display: "flex", alignItems: "center" }}
            title="ホーム"
            aria-label="home"
          >
            <Logo height={isMobile ? 56 : 72} />
          </Box>
          <Box sx={{ flex: 1 }} />
          <Link
            href="https://disclosure.edinet-fsa.go.jp/"
            target="_blank"
            rel="noreferrer"
          >
            EDINET
          </Link>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 2 }}>
        {!apiKey.trim() ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            EDINET APIキーが未設定です。ローカルなら `.env.local` の
            `VITE_EDINET_API_KEY`、Pagesなら GitHub Secrets を確認してください。
          </Alert>
        ) : null}

        <TextField
          size="small"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder="銘柄名 / 証券コードで検索"
          fullWidth
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />

        <Box sx={{ mt: 2, width: "100%", position: "relative" }}>
          {isMobile ? (
            <Box sx={{ border: "1px solid rgba(0,0,0,0.12)", borderRadius: 1 }}>
              <List disablePadding dense>
                {rows.slice(0, 200).map((row) => (
                  <ListItemButton
                    key={row.id}
                    onClick={() => {
                      setSelectedCompany(row as Company);
                      setDialogOpen(true);
                    }}
                  >
                    <ListItemText
                      primary={
                        <Typography variant="body1" sx={{ fontWeight: 700 }}>
                          {row.name}
                        </Typography>
                      }
                      secondary={`${row.secCode4} / ${row.market}`}
                    />
                  </ListItemButton>
                ))}
              </List>
              {rows.length > 200 ? (
                <Box sx={{ p: 1, color: "text.secondary", fontSize: 12 }}>
                  モバイル表示は最大200件まで表示します。検索で絞り込んでください。
                </Box>
              ) : null}
            </Box>
          ) : (
            <Box sx={{ height: 680 }}>
              <DataGrid
                rows={rows}
                columns={columns}
                disableRowSelectionOnClick
                density="compact"
                onRowClick={(params) => {
                  setSelectedCompany(params.row as Company);
                  setDialogOpen(true);
                }}
                initialState={{
                  pagination: { paginationModel: { pageSize: 25, page: 0 } },
                  sorting: { sortModel: [{ field: "secCode4", sort: "asc" }] },
                }}
                pageSizeOptions={[25, 50, 100]}
              />
            </Box>
          )}

          {busy ? (
            <Box
              sx={{
                position: "absolute",
                inset: 0,
                display: "grid",
                placeItems: "center",
                bgcolor: "rgba(255,255,255,0.6)",
                zIndex: 10,
              }}
            >
              <Stack alignItems="center" spacing={1}>
                <CircularProgress />
                <Typography variant="body2">処理中…</Typography>
              </Stack>
            </Box>
          ) : null}
        </Box>

        <YearDownloadsDialog
          open={dialogOpen}
          company={selectedCompany}
          apiKey={apiKey}
          onClose={() => setDialogOpen(false)}
          onConfirm={handleConfirmDownload}
        />

        {snackbar ? (
          <Snackbar
            open
            autoHideDuration={6000}
            onClose={() => setSnackbar(null)}
            anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
          >
            <Alert
              onClose={() => setSnackbar(null)}
              severity={snackbar.severity}
              variant="filled"
            >
              {snackbar.message}
            </Alert>
          </Snackbar>
        ) : null}
      </Box>
    </Box>
  );
}

