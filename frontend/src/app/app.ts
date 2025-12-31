import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App {
  file: File | null = null;
  uploading = false;  
  textPreview = '';
  question = '';
  asking = false;
  answer = '';
  language = 'English';
  languages = ['English', 'Tamil', 'Hindi'];

  constructor(private http: HttpClient) {}

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.file = input.files[0];
    }
  }

  upload() {
    if (!this.file) return;
    this.uploading = true;

    const formData = new FormData();
    formData.append('file', this.file);

    this.http.post('http://127.0.0.1:5000/upload', formData, { responseType: 'text' })
      .subscribe({
        next: (res: string) => {
          this.textPreview = res;
          this.uploading = false;
        },
        error: () => this.uploading = false
      });
  }

  ask() {
    if (!this.question) return;
    this.asking = true;

    this.http.post<{answer: string}>('http://127.0.0.1:5000/ask', {
      question: this.question,
      language: this.language
    }).subscribe({
      next: (res) => {
        this.answer = res.answer;
        this.asking = false;
      },
      error: () => this.asking = false
    });
  }
}

