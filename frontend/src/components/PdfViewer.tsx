import { useEffect, useMemo, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

type PdfViewerProps = {
    pdfUrl: string | null;
    pageNumber: number | null;
    highlightText: string | null;
};

function escapeRegExp(value: string) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export default function PdfViewer({ pdfUrl, pageNumber, highlightText }: PdfViewerProps) {
    const [numPages, setNumPages] = useState<number | null>(null);
    const [internalPage, setInternalPage] = useState(1);
    const [showAllPages, setShowAllPages] = useState(false);
    const containerRef = useRef<HTMLDivElement | null>(null);
    const highlightRegex = useMemo(() => {
        if (!highlightText?.trim()) {
            return null;
        }
        return new RegExp(escapeRegExp(highlightText.trim()), "gi");
    }, [highlightText]);

    useEffect(() => {
        if (pageNumber) {
            setInternalPage(pageNumber);
        }
    }, [pageNumber]);

    useEffect(() => {
        if (!showAllPages || !pageNumber || !containerRef.current) {
            return;
        }
        const target = containerRef.current.querySelector(
            `[data-page="${pageNumber}"]`
        ) as HTMLElement | null;
        if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }, [pageNumber, showAllPages]);

    const activePage = pageNumber ?? internalPage;

    return (
        <div className="pdf-viewer" ref={containerRef}>
            {pdfUrl ? (
                <Document
                    file={pdfUrl}
                    onLoadSuccess={(result) => {
                        setNumPages(result.numPages);
                        setInternalPage(1);
                    }}
                >
                    <div className="pdf-toolbar">
                        <button
                            type="button"
                            onClick={() => setInternalPage((page) => Math.max(1, page - 1))}
                            disabled={activePage <= 1}
                        >
                            Prev
                        </button>
                        <span>
                            Page {activePage} {numPages ? `of ${numPages}` : ""}
                        </span>
                        <button
                            type="button"
                            onClick={() =>
                                setInternalPage((page) =>
                                    numPages ? Math.min(numPages, page + 1) : page + 1
                                )
                            }
                            disabled={numPages ? activePage >= numPages : false}
                        >
                            Next
                        </button>
                        <button
                            type="button"
                            onClick={() => setShowAllPages((value) => !value)}
                        >
                            {showAllPages ? "Single page" : "All pages"}
                        </button>
                    </div>
                    {showAllPages && numPages
                        ? Array.from({ length: numPages }, (_, index) => {
                            const page = index + 1;
                            return (
                                <div key={page} data-page={page} className="pdf-page">
                                    <Page
                                        pageNumber={page}
                                        renderTextLayer
                                        renderAnnotationLayer={false}
                                        customTextRenderer={(textItem) => {
                                            if (!highlightRegex) {
                                                return textItem.str;
                                            }
                                            return textItem.str.replace(highlightRegex, (match) => {
                                                return `<mark class="pdf-highlight">${match}</mark>`;
                                            });
                                        }}
                                    />
                                </div>
                            );
                        })
                        : (
                            <div data-page={activePage} className="pdf-page">
                                <Page
                                    pageNumber={activePage}
                                    renderTextLayer
                                    renderAnnotationLayer={false}
                                    customTextRenderer={(textItem) => {
                                        if (!highlightRegex) {
                                            return textItem.str;
                                        }
                                        return textItem.str.replace(highlightRegex, (match) => {
                                            return `<mark class="pdf-highlight">${match}</mark>`;
                                        });
                                    }}
                                />
                            </div>
                        )}
                </Document>
            ) : (
                <div className="placeholder">Upload a PDF to preview it here.</div>
            )}
        </div>
    );
}
