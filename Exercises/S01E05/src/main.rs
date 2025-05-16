use dotenv::dotenv;
use reqwest;
use std::env;
use std::fs::File;
use std::io::Write;
// use std::process::Command;
use serde_json::json;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    dotenv().ok();
    
    let api_key = env::var("DV_API_KEY").expect("DV_API_KEY not set");
    let url = format!("https://c3ntrala.ag3nts.org/data/{}/cenzura.txt", api_key);
    
    let response = reqwest::get(&url).await?;
    let content = response.text().await?;
    
    let mut file = File::create("cenzura.txt")?;
    file.write_all(content.as_bytes())?;
    
    println!("{}", content);
    
    let text = std::fs::read_to_string("cenzura.txt")?;
    
    let prompt = format!(
        "Replace the following information in the text with the word \"CENZURA\":\n\n\
        * Name and surname (together, e.g. \"Jan Nowak\" -> \"CENZURA\").\n\
        * Age (e.g. \"32\" -> \"CENZURA\").\n\
        * City (e.g. \"Wrocław\" -> \"CENZURA\").\n\
        * Street and house number (together, e.g. \"ul. Szeroka 18\" -> \"ul. CENZURA\").\n\n\
        Keep the original text format (dots, commas, spaces). You are not allowed to edit the text.\n\n\
        Text:\n\
        ---\n\
        {}\n\
        ---",
        text
    );

    // Old local LLM code
    /*
    let mut child = Command::new("ollama")
        .args(&[
            "run",
            "deepseek-r1:32b",
            "--timeout", "50"
        ])
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()?;
    
    if let Some(ref mut stdin) = child.stdin {
        stdin.write_all(prompt.as_bytes())?;
    }
    
    let output = child.wait_with_output()?;
    let censored_text = String::from_utf8_lossy(&output.stdout);
    */

    let openai_key = env::var("OPENAI_API_KEY").expect("OPENAI_API_KEY not set");
    let client = reqwest::Client::new();
    
    let openai_response = client
        .post("https://api.openai.com/v1/chat/completions")
        .header("Authorization", format!("Bearer {}", openai_key))
        .header("Content-Type", "application/json")
        .json(&json!({
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a text censoring assistant. Your task is to replace personal information with the word CENZURA while maintaining the original text format. You have to output only the censored text, nothing else."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }))
        .send()
        .await?;

    let openai_json: serde_json::Value = openai_response.json().await?;
    let censored_text = openai_json["choices"][0]["message"]["content"]
        .as_str()
        .unwrap_or("Error: No response from OpenAI");
    
    let mut censored_file = File::create("censored.txt")?;
    censored_file.write_all(censored_text.as_bytes())?;

    let report_response = client.post("https://c3ntrala.ag3nts.org/report")
        .json(&json!({
            "task": "CENZURA",
            "apikey": api_key,
            "answer": censored_text
        }))
        .send()
        .await?;

    let report_json: serde_json::Value = report_response.json().await?;
    let result = if report_json["code"].as_i64().unwrap_or(-1) < 0 {
        println!("Error: Invalid server response: {:?}", report_json);
        "Error: No result from server"
    } else {
        report_json["message"].as_str().unwrap_or("Unknown response")
    };
    
    println!("Result: {}", result);
    println!("Censored text saved to censored.txt");
    
    Ok(())
} 