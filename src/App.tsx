import DownloadIcon from "@mui/icons-material/Download";
import SearchIcon from "@mui/icons-material/Search";
import {
  Alert,
  AppBar,
  Box,
  CircularProgress,
  IconButton,
  InputAdornment,
  Link,
  Snackbar,
  Stack,
  TextField,
  Toolbar,
} from "@mui/material";
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
  const apiKey = (import.meta.env.VITE_EDINET_API_KEY as string | undefined) ?? "";

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
    return base.filter((c) => tokens.every((t) => String(c._search).includes(t)));
  }, [companies, searchText]);

  const columns = useMemo<GridColDef[]>(
    () => [
      { field: "secCode4", headerName: "証券コード", width: 130, sortable: true },
      { field: "name", headerName: "銘柄名", flex: 1, minWidth: 320, sortable: true },
      { field: "market", headerName: "市場", width: 160, sortable: true },
      {
        field: "download",
        headerName: "有報",
        width: 90,
        sortable: false,
        filterable: false,
        renderCell: (params) => (
          <IconButton
            aria-label="download"
            onClick={() => {
              setSelectedCompany(params.row as Company);
              setDialogOpen(true);
            }}
          >
            <DownloadIcon />
          </IconButton>
        ),
      },
    ],
    [],
  );

  async function handleConfirmDownload(options: YearDownloadOptions) {
    if (!selectedCompany) return;
    if (!apiKey.trim()) {
      setSnackbar({
        severity: "error",
        message: "EDINET APIキーが未設定です（.env.local の VITE_EDINET_API_KEY）。",
      });
      return;
    }
    setDialogOpen(false);

    try {
      setBusy(true);
      const docs: Array<Pick<EdinetDocument, "docID" | "submitDateTime" | "docDescription">> =
        options.docs && options.docs.length > 0 ? options.docs : [];

      if (docs.length === 0) {
        setSnackbar({
          severity: "info",
          message: "対象年度の有報が見つかりませんでした（未収録の可能性があります）。",
        });
        return;
      }

      setSnackbar({ severity: "info", message: `ダウンロード中…（${docs.length}件）` });
      for (const doc of docs) {
        const submitted =
          (doc.submitDateTime ?? "").split(" ")[0] || String(options.year);
        const desc = doc.docDescription ?? "有報";
        const ext = options.fileType === 2 ? "pdf" : "zip";
        const filename = sanitizeFileName(
          `${selectedCompany.secCode4}_${selectedCompany.name}_${submitted}_${desc}_${doc.docID}.${ext}`,
        );
        const blob = await downloadDocumentBlob(doc.docID, options.fileType, apiKey);
        await downloadBlob(blob, filename);
      }

      setSnackbar({ severity: "success", message: `ダウンロード完了: ${docs.length}件` });
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
        <Toolbar sx={{ gap: 2, minHeight: 72 }}>
          <Box
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            sx={{ cursor: "pointer", display: "flex", alignItems: "center" }}
            title="ホーム"
            aria-label="home"
          >
            <Logo height={90} />
          </Box>
          <Box sx={{ flex: 1 }} />
          <Link href="https://disclosure.edinet-fsa.go.jp/" target="_blank" rel="noreferrer">
            EDINET
          </Link>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 2 }}>
        {!apiKey.trim() ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            EDINET APIキーが未設定です。`mr-insight/.env.local` に `VITE_EDINET_API_KEY`
            を設定して再起動してください。
          </Alert>
        ) : null}

        <TextField
          size="small"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder="銘柄名 or 証券コードで検索"
          fullWidth
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />

        <Box sx={{ mt: 2, height: 680, width: "100%", position: "relative" }}>
          <DataGrid
            rows={rows}
            columns={columns}
            disableRowSelectionOnClick
            density="compact"
            initialState={{
              pagination: { paginationModel: { pageSize: 25, page: 0 } },
              sorting: { sortModel: [{ field: "secCode4", sort: "asc" }] },
            }}
            pageSizeOptions={[25, 50, 100]}
          />

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
                <Box component="span" sx={{ fontSize: 14 }}>
                  処理中…
                </Box>
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

