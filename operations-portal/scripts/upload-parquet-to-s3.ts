import { readFileSync, readdirSync } from 'fs';
import { storagePut } from '../server/storage';
import { getDb } from '../server/db';
import { dataProducts } from '../drizzle/schema';
import { eq } from 'drizzle-orm';

/**
 * Upload all ETF Parquet files from UltraCore repo to S3
 * and update database with S3 URLs for production-grade data mesh
 */
async function uploadParquetFilesToS3() {
  console.log('🚀 Starting Parquet file upload to S3...\n');

  const db = await getDb();
  if (!db) {
    console.error('❌ Database not available');
    process.exit(1);
  }

  const parquetDir = '/home/ubuntu/UltraCore/data/etf/historical';
  const files = readdirSync(parquetDir).filter(f => f.endsWith('.parquet'));

  console.log(`📊 Found ${files.length} Parquet files to upload\n`);

  let successCount = 0;
  let errorCount = 0;

  for (const filename of files) {
    const ticker = filename.replace('.parquet', '');
    const filePath = `${parquetDir}/${filename}`;

    try {
      console.log(`📤 Uploading ${ticker}.parquet...`);

      // Read the Parquet file
      const fileBuffer = readFileSync(filePath);
      const fileSizeBytes = fileBuffer.length;
      const fileSizeMB = (fileSizeBytes / 1024 / 1024).toFixed(2);

      // Upload to S3 with organized path
      const s3Key = `data-mesh/etf-historical/${ticker}.parquet`;
      const { url: s3Url } = await storagePut(s3Key, fileBuffer, 'application/octet-stream');

      console.log(`  ✅ Uploaded to S3: ${s3Url} (${fileSizeMB} MB)`);

      // Update database with S3 URL
      const result = await db
        .update(dataProducts)
        .set({
          s3Path: s3Url,
          sizeBytes: fileSizeBytes,
          lastUpdated: new Date(),
        })
        .where(eq(dataProducts.ticker, ticker));

      console.log(`  ✅ Updated database for ${ticker}\n`);
      successCount++;

    } catch (error) {
      console.error(`  ❌ Failed to upload ${ticker}:`, error);
      errorCount++;
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('📊 Upload Summary:');
  console.log(`  ✅ Success: ${successCount} files`);
  console.log(`  ❌ Errors: ${errorCount} files`);
  console.log(`  📦 Total: ${files.length} files`);
  console.log('='.repeat(60));
}

uploadParquetFilesToS3()
  .then(() => {
    console.log('\n✅ Parquet upload complete!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Upload failed:', error);
    process.exit(1);
  });
